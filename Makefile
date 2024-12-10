
docker: NFD
	docker build -f NFD/Dockerfile -t nfd-base --target build NFD/
	docker build -f Dockerfile -t nfd .
