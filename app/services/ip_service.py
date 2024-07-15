from app.db import Database
from bson import ObjectId

db = Database()

class IPService:
    @staticmethod
    def get_all_ips():
        return db.ips_collection.find()

    @staticmethod
    def add_ip(ip_address, tag):
        db = Database()
        if db.ips_collection.find_one({"ip_address": ip_address}):
            return "ip_exists"
        db.ips_collection.insert_one({"ip_address": ip_address, "tag": tag})
        return "ip_added"

    @staticmethod
    def delete_ip(ip_id):
        db = Database()
        result = db.ips_collection.delete_one({"_id": ObjectId(ip_id)})
        return result.deleted_count > 0

    @staticmethod
    def get_allowed_ips():
        db = Database()
        ips = db.ips_collection.find({}, {"ip_address": 1, "_id": 0})
        return [ip['ip_address'] for ip in ips]

