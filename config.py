import os

class Config:
    SECRET_KEY = 'shivam_attendnce_models'

    if os.environ.get("RENDER") == "true":
        SQLALCHEMY_DATABASE_URI = 'postgresql://root:CGIf9UBARjkPDGij5fLHzIN0Rl2Mmcac@dpg-d1vku6h5pdvs73e84ls0-a/attendance_db_38bl'
    else:
        SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:12345@localhost:5432/attendance_db'

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(os.getcwd(), 'app', 'static', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024

