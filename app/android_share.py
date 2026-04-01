from __future__ import annotations

import os
import re
import tempfile
import time

from kivy.utils import platform


def is_android_runtime() -> bool:
    return platform == "android"


def export_widget_png(widget, title: str) -> str:
    safe_title = re.sub(r"[^A-Za-z0-9._-]+", "_", title or "chart").strip("._") or "chart"
    file_path = os.path.join(tempfile.gettempdir(), f"{safe_title}_{int(time.time())}.png")
    widget.export_to_png(file_path)
    return file_path


def share_png_file(file_path: str, chooser_title: str = "Share chart") -> tuple[bool, str]:
    if not os.path.exists(file_path):
        return False, f"File not found: {file_path}"
    if not is_android_runtime():
        return False, file_path

    try:
        from jnius import autoclass, cast

        PythonActivity = autoclass("org.kivy.android.PythonActivity")
        Intent = autoclass("android.content.Intent")
        String = autoclass("java.lang.String")
        ContentValues = autoclass("android.content.ContentValues")
        MediaStoreImagesMedia = autoclass("android.provider.MediaStore$Images$Media")
        MediaStoreMediaColumns = autoclass("android.provider.MediaStore$MediaColumns")
        Environment = autoclass("android.os.Environment")
        FileInputStream = autoclass("java.io.FileInputStream")
        BuildVersion = autoclass("android.os.Build$VERSION")

        activity = PythonActivity.mActivity
        resolver = activity.getContentResolver()
        values = ContentValues()
        values.put(MediaStoreMediaColumns.DISPLAY_NAME, String(os.path.basename(file_path)))
        values.put(MediaStoreMediaColumns.MIME_TYPE, String("image/png"))
        if int(BuildVersion.SDK_INT) >= 29:
            values.put(MediaStoreMediaColumns.RELATIVE_PATH, String(f"{Environment.DIRECTORY_PICTURES}/RotorProtek"))

        target_uri = resolver.insert(MediaStoreImagesMedia.EXTERNAL_CONTENT_URI, values)
        if target_uri is None:
            raise RuntimeError("Android no devolvio un destino para guardar la imagen.")

        input_stream = FileInputStream(file_path)
        output_stream = resolver.openOutputStream(target_uri)
        if output_stream is None:
            raise RuntimeError("Android no pudo abrir el flujo de salida de la imagen.")
        try:
            input_stream.transferTo(output_stream)
        finally:
            try:
                input_stream.close()
            finally:
                output_stream.close()

        send_intent = Intent(Intent.ACTION_SEND)
        send_intent.setType("image/png")
        send_intent.putExtra(Intent.EXTRA_STREAM, cast("android.os.Parcelable", target_uri))
        send_intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
        chooser = Intent.createChooser(send_intent, String(chooser_title))
        activity.startActivity(chooser)
        return True, str(target_uri)
    except Exception as exc:
        return False, str(exc)
