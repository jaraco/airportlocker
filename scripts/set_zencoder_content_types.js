db.luggage.files.update(
    {
        "zencoder_outputs": {
            $elemMatch: {
                "url": /\.mp4$/,
                "state": "finished",
            }
        }
    },
    { $set: { "zencoder_outputs.$.contentType": "video/mp4" } },
    { multi: true }
)

db.luggage.files.update(
    {
        "zencoder_outputs": {
            $elemMatch: {
                "url": /\.webm$/,
                "state": "finished",
            }
        }
    },
    { $set: { "zencoder_outputs.$.contentType": "video/webm" } },
    { multi: true }
)

db.luggage.files.update(
    {
        "zencoder_outputs": {
            $elemMatch: {
                "url": /\.ogg$/,
                "state": "finished",
            }
        }
    },
    { $set: { "zencoder_outputs.$.contentType": "video/ogg" } },
    { multi: true }
)

db.luggage.files.update(
    {
        "zencoder_outputs": {
            $elemMatch: {
                "url": /\.3gp$/,
                "state": "finished",
            }
        }
    },
    { $set: { "zencoder_outputs.$.contentType": "video/3gp" } },
    { multi: true }
)

db.luggage.files.find(
    {
        "zencoder_outputs": {
            $elemMatch: {
                "contentType": {$exists: 0},
                "state": "finished",
            }
        }
    }
).count()
