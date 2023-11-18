from locust import FastHttpUser, constant_throughput, task
import datetime
from random import randrange, choice
import uuid


# A list of all tracker JWTs available for sending data.
tracker_jwts = []

# A single instance of this class represents 100 users. 
# A single user is estimated to send 1 update every 20 seconds.
# The weight of this class is 1 to create the appropriate tracker/user ratio.
class CnatUser(FastHttpUser):
    weight = 1
    wait_time =  constant_throughput((1/20)*100)
    email = None
    password = "password"
    jwt = None
    tracker_ids = None
    
    # the user initialized with the following steps:
    # - Generates a new email address.
    # - Registers a new user.
    # - Authenticated the user to get a user JWT.
    # - Registers a new tracker.
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
                        tracker_jwts.append(register_tracker_res.js['accessToken'])
    
    # Sends an authentication request.
    @task(4)
    def login(self):
        self.rest("POST", "/api/users/auth", json = {
            "email": self.email,
            "password": self.password
        })
    
    # Sends a tracker registration request.
    @task(1)
    def registerTracker(self):
        with self.rest("POST", "/api/trackers", json = {
            "name": "Test Tracker #" + str(len(self.tracker_ids)),
        },
        headers={'Authorization':'Bearer ' + self.jwt}) as register_tracker_res:
            self.tracker_ids.append(register_tracker_res.js['tracker']['id'])
            tracker_jwts.append(register_tracker_res.js['accessToken'])
    
    # Sends a get tracker request.
    @task(10)
    def getTracker(self):
        self.client.get("/api/trackers/%s" % choice(self.tracker_ids), name="/api/trackers/[id]", headers={'Authorization': 'Bearer ' + self.jwt})
    
    # Sends a get trackers request.
    @task(10)
    def getTrackers(self):
        self.client.get("/api/trackers", headers={'Authorization':'Bearer ' + self.jwt})
    
    # Sends a get tracker data request.
    @task(10)
    def getTrackerData(self):
        self.client.get("/api/trackers/%s/data" % choice(self.tracker_ids), name="/api/trackers/[id]/data", headers={'Authorization':'Bearer ' + self.jwt})
    
    # Sends a get latest trackers data request.
    @task(5)
    def getLatestTrackersData(self):
        self.client.get("/api/trackers/data/latest", headers={'Authorization':'Bearer ' + self.jwt})

    # Deletes all tracker and tracker data at the end of the test
    def on_stop(self):
        self.rest("DELETE", "/api/users", json = {
            "email": self.email,
            "password": self.password
        })

# A single instance of this class represents 100 trackers. 
# A single tracker is estimated to send 1 update every 20 minutes.
# The weight of this class is 100 to create the appropriate tracker/user ratio.
class CnatTracker(FastHttpUser):
    weight = 100
    wait_time =  constant_throughput((1/(20*60))*100)

    # Registers random generated tracker data using one of the tracker JWTs available.
    @task(1)
    def registerTrackerData(self):
        if (len(tracker_jwts) > 0):
            self.client.post("/api/trackers/data",
                json={
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
                },
                headers={'Authorization':'Bearer ' + choice(tracker_jwts)
            })
