db = db.getSiblingDB('admin');

db.auth(process.env.MONGO_INITDB_ROOT_USERNAME, process.env.MONGO_INITDB_ROOT_PASSWORD);

db = db.getSiblingDB('boat_tracker');

if (db.getUser(process.env.MONGO_INITDB_ROOT_USERNAME) == null) {
    db.createUser({
        user: process.env.MONGO_INITDB_ROOT_USERNAME,
        pwd: process.env.MONGO_INITDB_ROOT_PASSWORD,
        roles: [
            { role: "readWrite", db: "boat_tracker" },
            { role: "dbAdmin", db: "boat_tracker" }
        ]
    });
}

// Create collections
db.createCollection('booking_data_mmk');
db.createCollection('update_log');
db.createCollection('competitor'); 