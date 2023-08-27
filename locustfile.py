from locust import FastHttpUser, constant_throughput, task
import json
import datetime
from random import randrange, choice
import uuid


class CnatUser(FastHttpUser):
    wait_time =  constant_throughput(1.1)
    email = None
    password = "password"
    jwt = None
    tracker_ids = None
    tracker_jwts = None
    
    def on_start(self):
        self.email = str(uuid.uuid4()) + "@test.com"
        
        with self.rest("POST", "/api/users", json={
            "email": self.email,
            "password": self.password,
            "firstName": "fn",
            "lastName": "ln"
        }) as register_res:
            if (register_res != None):
                with self.rest("POST", "/api/users/auth", json={
                    "email": self.email,
                    "password": self.password,
                }) as login_res:
                    self.jwt = login_res.js['accessToken']
                    with self.rest("POST", "/api/trackers", json = {
                        "name": "Test Tracker #1",
                    },
                    headers={'Authorization':'Bearer ' + self.jwt}) as register_tracker_res:
                        self.tracker_ids = [register_tracker_res.js['tracker']['id']]
                        self.tracker_jwts = [register_tracker_res.js['accessToken']]
    
    @task(4)
    def login(self):
        # self.client.get("/login")
        self.rest("POST", "/api/users/auth", json = {
            "email": self.email,
            "password": self.password
        })
    
    @task(1)
    def registerTracker(self):
        # self.client.get("/user-area/dashboard")
        with self.rest("POST", "/api/trackers", json = {
            "name": "Test Tracker #" + str(len(self.tracker_ids)),
        },
        headers={'Authorization':'Bearer ' + self.jwt}) as register_tracker_res:
            self.tracker_ids.append(register_tracker_res.js['tracker']['id'])
            self.tracker_jwts.append(register_tracker_res.js['accessToken'])
    
    @task(10)
    def getTracker(self):
        # self.client.get("/user-area/dashboard")
        self.client.get("/api/trackers/" + choice(self.tracker_ids), headers={'Authorization': 'Bearer ' + self.jwt})
    
    @task(10)
    def getTrackers(self):
        # self.client.get("/user-area/dashboard")
        self.client.get("/api/trackers", headers={'Authorization':'Bearer ' + self.jwt})
    
    @task(10)
    def getTrackerData(self):
        # self.client.get("/user-area/dashboard")
        self.client.get("/api/trackers/" + choice(self.tracker_ids)+"/data", headers={'Authorization':'Bearer ' + self.jwt})
    
    @task(5)
    def getLatestTrackersData(self):
        # self.client.get("/user-area/dashboard")
        self.client.get("/api/trackers/data/latest", headers={'Authorization':'Bearer ' + self.jwt})
    
    # @task(1)
    # def deleteTracker(self):
    #     self.client.get("/user-area/dashboard")
    #     self.client.delete("/trackers/"+self.tracker_id, headers={'Authorization':'Bearer ' + self.jwt})

    @task(400)
    def registerTrackerData(self):
        self.client.post("/api/trackers/data", json={
            "data": {
                "temperature": randrange(-100, 100),
                "pressure": randrange(80000, 100000),
                "humidity": randrange(0, 100),
                "uv": randrange(0, 10),
                "coordinates": [
                    randrange(-90, 90),
                    randrange(-180, 180)
                ]
            },
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z"
            },headers={'Authorization':'Bearer ' + choice(self.tracker_jwts)})
    
    def on_stop(self):
        with self.rest("DELETE", "/api/users", json = {
            "email": self.email,
            "password": self.password
        }) as delete_res:
            pass

