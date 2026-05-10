from datetime import datetime

class DocumentRecord:
    @staticmethod
    def create(filename, user_id):
        import database.db as db_module
        doc = {
            'filename': filename,
            'user_id': user_id,
            'processed_at': datetime.utcnow()
        }
        result = db_module.db.documents.insert_one(doc)
        doc['_id'] = result.inserted_id
        doc['id'] = str(doc['_id'])
        return doc
