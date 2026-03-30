# Build Android

## Requisitos

- Linux o WSL2 Ubuntu para ejecutar Buildozer.
- Python 3.10 o 3.11 en el entorno de build.
- Java JDK 17.
- Dependencias de sistema habituales de Buildozer y python-for-android.

## Dependencias Python de la app

- `python3`
- `kivy==2.3.0`
- `kivymd==1.2.0`
- `numpy`
- `pyjnius`

## Comandos de build

```bash
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install buildozer cython
buildozer android debug
```

Para limpiar una build rota:

```bash
buildozer android clean
buildozer android debug
```

Para instalar en un dispositivo conectado por ADB:

```bash
buildozer android deploy run
```

## Comprobaciones previas

- Verifica que `main.py` arranca la app Kivy.
- Verifica que `buildozer.spec` incluye `pyjnius`.
- Verifica que no queda `pandas` en la app movil.
- Verifica que el selector Android usa `ACTION_OPEN_DOCUMENT`.
- Verifica que los CSV de prueba cargan con `app.csv_loader`.

## Notas

- La seleccion de archivos en Android usa Storage Access Framework y copia el CSV a la cache interna de la app antes de parsearlo.
- No se solicitan permisos de almacenamiento porque el acceso se hace mediante el selector de documentos del sistema.
- Si quieres icono Android real, falta aportar un `png` cuadrado del logo para declararlo en `buildozer.spec`.
