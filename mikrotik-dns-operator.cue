package mikrotik_dns_operator

import (
	"dagger.io/dagger"
	"universe.dagger.io/docker"
)

dagger.#Plan & {
	client: {
		filesystem: {
			"./": read: contents: dagger.#FS
		}
		network: "unix:///var/run/docker.sock": connect: dagger.#Socket
	}

	actions: {
		test: {
			deps: docker.#Build & {
			  steps: [
				  docker.#Pull & {
					  source: "python:3.8"
					},
					docker.#Copy & {
						contents: client.filesystem."./".read.contents
						dest:     "/app"
					},
					docker.#Run & {
						command: {
							name: "pip"
							args: ["install", "poetry"]
						}
					},
					docker.#Set & {
						config: workdir: "/app"
					},
					docker.#Run & {
						command: {
							name: "poetry"
							args: ["config", "virtualenvs.create", "false"]
						}
					},
					docker.#Run & {
						command: {
							name: "poetry"
							args: ["install", "--no-interaction" , "--no-ansi"]
						}
					}
				]
			}
			test: docker.#Run & {
  		  input: deps.output
  		  command: {
  			  name: "pytest"
  		  }
  	  }
		}
		build: docker.#Dockerfile & {
			source: client.filesystem."./".read.contents
		}
		push: docker.#Push & {
			image: build.output
			dest: "sebastianhutter/miktrotik-dns-operator"
		}
	}
}