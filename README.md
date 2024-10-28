# NDN Traceroute

This project implements an **NDN Traceroute Client** and a **Simple Producer** based on the ICN Traceroute Protocol Specification as defined in [RFC 9507](https://www.rfc-editor.org/rfc/rfc9507.html).

**Note:** The Simple Producer is included for testing and development purposes only.

## Prerequisites

- **Operating System**: macOS, Linux, or any UNIX-like system.
- **NDN Platform**:
  - [ndn-cxx library](https://github.com/named-data/ndn-cxx)
  - [NFD](https://github.com/named-data/NFD) (todo: this needs to be updated to use custom forwarder)
- **C++ Compiler**: Support for C++17 (e.g., GCC 7+, Clang 6+).
- **CMake**: Version 3.12 or higher.

## Building the Project

### 1. Clone the Repository

```bash
git clone https://github.com/saifulislampi/ndn-traceroute.git
cd ndn-traceroute
```

### 2. Install NDN Dependencies

Ensure that `ndn-cxx` and `NFD` are installed on your system. Follow the installation instructions provided in the official documentation.

### 3. Build the Applications

Create a build directory and compile the project using CMake:

```bash
mkdir build
cd build
cmake ..
make -j$(nproc)  # For Linux
# or
make -j$(sysctl -n hw.logicalcpu)  # For macOS
```

This will build both the Traceroute Client and the Simple Producer executables.

## Running the Applications

### Starting NFD

Before running the applications, ensure that the NDN Forwarding Daemon (NFD) is running:

```bash
nfd-start
```

Verify that NFD is running:

```bash
nfd-status
```

### Running the Simple Producer

In one terminal, start the Simple Producer:

```bash
cd build/producer
./simple-producer
```

You should see output indicating that the producer is listening for Interests:

```plaintext
SimpleProducer: Listening for Interests on /example/test/traceroute
```

### Running the Traceroute Client

In another terminal, run the Traceroute Client:

```bash
cd build/client
./traceroute-client /example/test 5
```

Replace `/example/test` with the target name you wish to trace, and `5` with the maximum HopLimit (optional, defaults to 30).

**Sample Output:**

```plaintext
Sent Interest with HopLimit: 1
Hop 1, RTT: 5 ms, Forwarder: /example/producer, Reply Code: 4
Sent Interest with HopLimit: 2
Hop 2, RTT: 6 ms, Forwarder: /example/producer, Reply Code: 4
...
```

### Notes

- The Traceroute Client sends Interests with increasing HopLimits to discover each hop along the path to the target name.
- The Simple Producer responds to traceroute Interests matching `/example/test/traceroute`.
- Ensure that both applications are using the same prefix.
