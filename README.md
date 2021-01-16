```bash
docker build -t autoproxy .
```

```bash
docker create -t -i \
    -v /var/run/docker.sock:/var/run/docker.sock:ro \
    -v <le_data_path>:/etc/letsencrypt \
    --name autoproxy -p 80:80 -p 443:443 autoproxy
```

```bash
docker network connect some-network autoproxy
```

```bash
docker start autoproxy
```
