import json
import os

CONFIG_FILE = "base.json"


def get_config_path():
    return os.path.join(os.path.dirname(__file__), CONFIG_FILE)

class Config:
    _instance = None
    def __init__(self):  
        return 
    
    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = cls.__new__(cls)

            config_path = get_config_path()
            if os.path.exists(config_path):      
                with open(config_path, 'r') as file:
                    try:
                        json_data = json.load(file)
                    except json.JSONDecodeError as e:
                        print(f"Error decoding JSON: {e}")            
                    cls.build_config(json_data)
            else:
                    print(f"The config file '{CONFIG_FILE}' does not exist.")
        return cls._instance

    @classmethod
    def build_config(self, json_data):
        if 'OPENALEX_API_URL' in json_data:
            self.base_url = json_data["OPENALEX_API_URL"]

        self.use_redis = 'USE_REDIS' in json_data and json_data["USE_REDIS"]
    
    @classmethod
    def get_base_url(cls):
        if cls.base_url:
            return cls.base_url
        
    @classmethod
    def get_use_redis(cls):
        if cls.use_redis:
            return cls.use_redis
        
