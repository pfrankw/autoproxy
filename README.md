# Do it
```shell
docker run -d \
	-e VIRTUAL_HOST=example.com,www.example.com \
	-e WANT_SSL=1 \
	-e HTTP_PORT=8080 \
	some-options \
	some-container
```

# THEN

```shell
docker run -d \
	--name autoproxy \
	-p 80:80 \
	-p 443:443 \
	-v /var/run/docker.sock:/var/run/docker.sock:ro \
	-v <le_data_path>:/etc/letsencrypt \
	autoproxy
```

# OR


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


# Enjoy
auto routed HTTP containers and automatic letsencrypt on them
