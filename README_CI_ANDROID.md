# CI Android

Este repositorio ya incluye una compilacion automatica de APK con GitHub Actions.

## Archivo de workflow

- `.github/workflows/android-apk.yml`
- `.github/workflows/android-apk-release.yml`

## Que hace el workflow

1. Usa `ubuntu-22.04`.
2. Instala `Python 3.11`.
3. Instala `Java 17`.
4. Instala dependencias de sistema para Buildozer y python-for-android.
5. Instala herramientas Python fijadas en `requirements-buildozer.txt`.
6. Ejecuta `buildozer android debug`.
7. Publica `bin/*.apk` como artefacto descargable.

## Como usarlo en GitHub

1. Sube el repositorio a GitHub.
2. Entra en la pestana `Actions`.
3. Abre el workflow `Android APK`.
4. Pulsa `Run workflow`.
5. Espera a que termine la build.
6. Descarga el artefacto `rotorprotek-android-apk`.

Tambien se ejecuta automaticamente en:

- `push` a `main`
- `push` a `master`
- `pull_request`

## Secretos necesarios

Para la APK debug actual:

- no hace falta ningun secret

Para una APK release firmada en el futuro:

- keystore en base64
- alias
- password del keystore
- password de la clave

Nombres exactos de secrets para el workflow release:

- `ANDROID_KEYSTORE_BASE64`
- `ANDROID_KEYSTORE_PASSWORD`
- `ANDROID_KEY_ALIAS`
- `ANDROID_KEY_PASSWORD`

Eso no es necesario para obtener una APK funcional de prueba descargable.

## Ajustes de reproducibilidad

Las herramientas de build quedan fijadas en:

- `requirements-buildozer.txt`

Versiones fijadas:

- `buildozer==1.5.0`
- `Cython==0.29.36`
- `virtualenv==20.26.6`

El workflow tambien cachea:

- `.buildozer`
- `~/.buildozer`
- `~/.gradle`

## Archivos que controlan la build

- `buildozer.spec`
- `requirements-buildozer.txt`
- `.github/workflows/android-apk.yml`
- `.github/workflows/android-apk-release.yml`

## Resultado esperado

Si la build termina correctamente, GitHub Actions generara una APK debug en:

- `bin/*.apk`

y la subira como artefacto descargable.

## Problemas tipicos

- Primera build lenta: es normal, descarga SDK, NDK y toolchains.
- Fallos temporales de red en GitHub Actions: relanza el workflow.
- Si cambias dependencias Kivy o Android, revisa `buildozer.spec` y `requirements-buildozer.txt`.
- Si quieres firma release, hace falta anadir secrets y un paso extra de firmado.

## Comprobacion minima antes de subir

- `main.py` arranca la app Kivy.
- `buildozer.spec` contiene dependencias Android finales.
- La app movil no depende de `pandas`.
- El selector Android esta implementado en `app/android_file_picker.py`.
- `buildozer.spec` excluye carpetas locales pesadas del repo como `build`, `old` y los CSV de prueba.
