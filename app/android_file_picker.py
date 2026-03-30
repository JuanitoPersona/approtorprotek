from __future__ import annotations

import os
import re
import time
from typing import Callable

from kivy.clock import Clock
from kivy.utils import platform


def is_android_runtime() -> bool:
    return platform == "android"


class AndroidCsvPicker:
    def __init__(
        self,
        on_success: Callable[[str, str], None],
        on_cancel: Callable[[], None],
        on_error: Callable[[str], None],
        request_code: int = 41021,
    ) -> None:
        self.on_success = on_success
        self.on_cancel = on_cancel
        self.on_error = on_error
        self.request_code = request_code
        self._bound = False

    def open(self) -> None:
        if not is_android_runtime():
            self._dispatch_error("El selector Android solo puede abrirse en un dispositivo Android.")
            return

        try:
            from android import activity
            from jnius import autoclass

            Intent = autoclass("android.content.Intent")
            PythonActivity = autoclass("org.kivy.android.PythonActivity")

            if not self._bound:
                activity.bind(on_activity_result=self._on_activity_result)
                self._bound = True

            intent = Intent(Intent.ACTION_OPEN_DOCUMENT)
            intent.addCategory(Intent.CATEGORY_OPENABLE)
            intent.setType("*/*")
            intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION | Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION)
            PythonActivity.mActivity.startActivityForResult(intent, self.request_code)
        except Exception as exc:
            self._dispatch_error(f"No se pudo abrir el selector de archivos: {exc}")

    def _on_activity_result(self, request_code, result_code, intent) -> None:
        if int(request_code) != int(self.request_code):
            return

        self._unbind()
        try:
            from jnius import autoclass

            Activity = autoclass("android.app.Activity")
            if int(result_code) != int(Activity.RESULT_OK) or intent is None:
                self._dispatch_cancel()
                return

            uri = intent.getData()
            if uri is None:
                self._dispatch_cancel()
                return

            local_path, display_name = self._persist_csv_from_uri(uri, intent)
            self._dispatch_success(local_path, display_name)
        except Exception as exc:
            self._dispatch_error(f"No se pudo importar el archivo seleccionado: {exc}")

    def _persist_csv_from_uri(self, uri, intent) -> tuple[str, str]:
        from jnius import autoclass

        Intent = autoclass("android.content.Intent")
        OpenableColumns = autoclass("android.provider.OpenableColumns")
        PythonActivity = autoclass("org.kivy.android.PythonActivity")

        activity = PythonActivity.mActivity
        resolver = activity.getContentResolver()
        flags = intent.getFlags()
        take_flags = flags & (Intent.FLAG_GRANT_READ_URI_PERMISSION | Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION)
        try:
            resolver.takePersistableUriPermission(uri, take_flags)
        except Exception:
            pass

        display_name = self._resolve_display_name(resolver, uri, OpenableColumns)
        if not display_name.lower().endswith(".csv"):
            raise ValueError("El archivo seleccionado no tiene extension .csv")

        cache_dir = str(activity.getCacheDir().getAbsolutePath())
        safe_name = re.sub(r"[^A-Za-z0-9._-]+", "_", display_name) or f"startup_{int(time.time())}.csv"
        local_path = os.path.join(cache_dir, safe_name)
        self._copy_uri_to_file(resolver, uri, local_path)
        return local_path, display_name

    def _resolve_display_name(self, resolver, uri, openable_columns) -> str:
        cursor = None
        try:
            cursor = resolver.query(uri, None, None, None, None)
            if cursor is not None and cursor.moveToFirst():
                index = cursor.getColumnIndex(openable_columns.DISPLAY_NAME)
                if index >= 0:
                    name = cursor.getString(index)
                    if name:
                        return str(name)
        finally:
            if cursor is not None:
                cursor.close()

        last_segment = uri.getLastPathSegment()
        if last_segment:
            return str(last_segment)
        return f"startup_{int(time.time())}.csv"

    def _copy_uri_to_file(self, resolver, uri, local_path: str) -> None:
        stream = resolver.openInputStream(uri)
        if stream is None:
            raise RuntimeError("Android no pudo abrir el flujo del archivo seleccionado.")

        try:
            with open(local_path, "wb") as output_file:
                while True:
                    chunk = stream.read()
                    if chunk == -1:
                        break
                    output_file.write(bytes([chunk]))
        finally:
            stream.close()

    def _unbind(self) -> None:
        if not self._bound:
            return
        try:
            from android import activity

            activity.unbind(on_activity_result=self._on_activity_result)
        finally:
            self._bound = False

    def _dispatch_success(self, local_path: str, display_name: str) -> None:
        Clock.schedule_once(lambda *_: self.on_success(local_path, display_name), 0)

    def _dispatch_cancel(self) -> None:
        Clock.schedule_once(lambda *_: self.on_cancel(), 0)

    def _dispatch_error(self, message: str) -> None:
        Clock.schedule_once(lambda *_: self.on_error(message), 0)
