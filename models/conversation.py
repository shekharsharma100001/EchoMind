from datetime import datetime

class Conversation:
    @staticmethod
    def create(user_id, file_name, file_url):
        import database.db as db_module
        conv_doc = {
            'user_id': user_id,
            'file_name': file_name,
            'file_url': file_url,
            'transcription': None,
            'transcript': None,
            'diarization': None,
            'summary': None,
            'insights': None,
            'sentiment': None,
            'metrics': None,
            'speaker_analysis': None,
            'analysis_result': None,
            'qa_history': [],
            'upload_date': datetime.utcnow()
        }
        result = db_module.db.conversations.insert_one(conv_doc)
        conv_doc['_id'] = result.inserted_id
        conv_doc['id'] = str(conv_doc['_id'])
        return conv_doc
        
    @staticmethod
    def get(conv_id):
        from bson.objectid import ObjectId
        import database.db as db_module
        try:
            doc = db_module.db.conversations.find_one({'_id': ObjectId(conv_id)})
            if doc:
                doc['id'] = str(doc['_id'])
            return doc
        except Exception:
            return None

    @staticmethod
    def update(conv_id, updates):
        from bson.objectid import ObjectId
        import database.db as db_module
        try:
            db_module.db.conversations.update_one({'_id': ObjectId(conv_id)}, {'$set': updates})
            return True
        except Exception:
            return False
            
    @staticmethod
    def add_qa(conv_id, qa_pair):
        from bson.objectid import ObjectId
        import database.db as db_module
        try:
            db_module.db.conversations.update_one({'_id': ObjectId(conv_id)}, {'$push': {'qa_history': qa_pair}})
            return True
        except Exception:
            return False
            
    @staticmethod
    def delete(conv_id):
        from bson.objectid import ObjectId
        import database.db as db_module
        try:
            result = db_module.db.conversations.delete_one({'_id': ObjectId(conv_id)})
            return result.deleted_count > 0
        except Exception:
            return False
