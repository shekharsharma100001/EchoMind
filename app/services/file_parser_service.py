def build_upload_response(file_info: dict) -> dict:
    return {
        "message": "File uploaded successfully",
        "file_id": file_info["file_id"],
        "filename": file_info["original_filename"],
        "file_type": file_info["file_type"],
        "saved_path": file_info["saved_path"],
    }