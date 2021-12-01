docker rm -f solr-facade
docker image rm solr-facade:1

docker build --tag solr-facade:1 .
docker run --name solr-facade -p 8093:8093 -d solr-facade:1 

