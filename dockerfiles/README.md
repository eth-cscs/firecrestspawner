# Dockerfile to for the Hub

This is a dockerfile to build the image used for the deployment of the Hub.

The image can be found in DockerHub: [rsarm/jhub:2.0.0-f7t-x86_64](https://hub.docker.com/layers/rsarm/jhub/2.0.0-f7t-x86_64/images/sha256-3474b7295728c7a61caad03711c2ae64e0615ed8c9c6ae15f8e273d72c7b7027?context=explore).

## Notes

### Build for linux/amd64 on an arm64 macbook

From the based directory of the repo:

```bash
docker build -f dockerfiles/Dockerfile --platform linux/amd64 -t rsarm/jhub:2.0.0-f7t-x86_64 .
```
The dockerfile has a `COPY` that needs the repository to be in the build directory.

### Push 
```bash
docker login  # only once per shell
docker push rsarm/jhub:2.0.0-f7t-x86_64
```
