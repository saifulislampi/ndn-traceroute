
docker: NFD
	docker build -f NFD/Dockerfile -t nfd-build --target build NFD/
	docker build -f Dockerfile -t ndn-traceroute .
