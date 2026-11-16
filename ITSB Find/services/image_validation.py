import io
import uuid
from pathlib import Path

from PIL import Image, UnidentifiedImageError

MAX_DIM = 1280


def save_valid_image(file_storage, upload_folder, max_bytes, allowed_ext, required=True):
    """Validasi lalu simpan gambar. Return (filename | None, error | None)."""
    if file_storage is None or not file_storage.filename:
        return (None, "Foto wajib diunggah.") if required else (None, None)

    ext = file_storage.filename.rsplit(".", 1)[-1].lower() if "." in file_storage.filename else ""
    if ext not in allowed_ext:
        return None, "Format foto harus JPG, JPEG, atau PNG."

    data = file_storage.stream.read(max_bytes + 1)
    if len(data) > max_bytes:
        return None, "Ukuran foto maksimal 2 MB."
    if not data:
        return None, "File foto kosong."

    try:
        with Image.open(io.BytesIO(data)) as probe:
            probe.verify()
        img = Image.open(io.BytesIO(data))
        fmt = (img.format or "").upper()
        if fmt not in ("JPEG", "PNG"):
            return None, "Isi file bukan gambar JPG atau PNG yang valid."
        img.load()
    except (UnidentifiedImageError, OSError, SyntaxError, Image.DecompressionBombError):
        return None, "File tidak dapat dibaca sebagai gambar."

    img.thumbnail((MAX_DIM, MAX_DIM))
    folder = Path(upload_folder)
    folder.mkdir(parents=True, exist_ok=True)
    name = f"{uuid.uuid4().hex}.{'png' if fmt == 'PNG' else 'jpg'}"
    # Menyimpan ulang dari piksel menghapus EXIF/metadata dan payload tersembunyi.
    if fmt == "PNG":
        img.save(folder / name, "PNG", optimize=True)
    else:
        img.convert("RGB").save(folder / name, "JPEG", quality=85, optimize=True)
    return name, None
