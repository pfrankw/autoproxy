```shell
docker build -t autoproxy .
```

```shell
docker create -t -i \
    -v /var/run/docker.sock:/var/run/docker.sock:ro \
    -v <le_data_path>:/etc/letsencrypt \
    --name autoproxy -p 80:80 -p 443:443 autoproxy
```

```shell
docker network connect some-network autoproxy
```

```shell
docker start autoproxy
```
