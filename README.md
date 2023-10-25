# jelly-sync

Sync favorites, played, and playing between 2 servers. The synchronization is bidirectional



# How to run

## With podman/docker

```
podman run --rm -it localhost/jellyfinsync:latest  \
--username1 userone --jellyfin_url1 http://server1.example.com:8080 --jellyfin_username1 userone --jellyfin_password1 XXXXXXX \
--username2 usertwo --jellyfin_url2 http://server2.example.com:8080 --jellyfin_username2 usertwo --jellyfin_password2 YYYYYYY
```

## From source

```
pip install -r requirements.txt

python src/sync.py \
--username1 userone --jellyfin_url1 http://server1.example.com:8080 --jellyfin_username1 userone --jellyfin_password1 XXXXXXX \
--username2 usertwo --jellyfin_url2 http://server2.example.com:8080 --jellyfin_username2 usertwo --jellyfin_password2 YYYYYYY
```

## Aditional environment variables

`QUERY_LIMIT`: set the query size to the server, by default is 5000.
