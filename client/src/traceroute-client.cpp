#include <ndn-cxx/face.hpp>
#include <ndn-cxx/encoding/block-helpers.hpp>
#include <ndn-cxx/security/key-chain.hpp>
#include <ndn-cxx/util/random.hpp>
#include <iostream>
#include <chrono>
#include <unordered_map>
#include <string>
#include <cstdint>
#include <stdexcept>
#include <functional>

class TracerouteClient
{
public:
    TracerouteClient(const ndn::Name &targetName, uint8_t maxHopLimit);
    void run();

private:
    void sendTracerouteInterest();
    void onData(const ndn::Interest &interest, const ndn::Data &data);
    void onTimeout(const ndn::Interest &interest);
    void onNack(const ndn::Interest &interest, const ndn::lp::Nack &nack);

    ndn::Name m_targetName;
    ndn::Face m_face;
    ndn::KeyChain m_keyChain;

    uint8_t m_maxHopLimit;
    uint8_t m_currentHopLimit;

    std::unordered_map<ndn::Name, std::chrono::steady_clock::time_point> m_sentInterests; // Maps Nonce to send time
};

TracerouteClient::TracerouteClient(const ndn::Name &targetName, uint8_t maxHopLimit)
    : m_targetName(targetName),
      m_maxHopLimit(maxHopLimit),
      m_currentHopLimit(1)
{
}

void TracerouteClient::run()
{
    sendTracerouteInterest();
    m_face.processEvents();
}

void TracerouteClient::sendTracerouteInterest()
{
    if (m_currentHopLimit > m_maxHopLimit)
    {
        std::cout << "Reached maximum HopLimit. Traceroute completed." << std::endl;
        m_face.shutdown();
        return;
    }

    // Construct Interest Name
    ndn::Name interestName = m_targetName;
    interestName.append("traceroute");

    // Generate a random Nonce
    uint64_t nonce = ndn::random::generateWord64();

    // Append nonce to interest name
    interestName.appendNumber(nonce);

    // Create the interest
    ndn::Interest interest(interestName);
    interest.setMustBeFresh(true);
    interest.setNonce(nonce);
    interest.setHopLimit(m_currentHopLimit);

    // Record the send time
    m_sentInterests[interest.getName()] = std::chrono::steady_clock::now();

    m_face.expressInterest(interest,
                           std::bind(&TracerouteClient::onData, this, std::placeholders::_1, std::placeholders::_2),
                           std::bind(&TracerouteClient::onNack, this, std::placeholders::_1, std::placeholders::_2),
                           std::bind(&TracerouteClient::onTimeout, this, std::placeholders::_1));

    std::cout << "Sent Interest with HopLimit: " << static_cast<int>(m_currentHopLimit) << std::endl;

    // Increment HopLimit for next Interest
    ++m_currentHopLimit;
}

void TracerouteClient::onData(const ndn::Interest &interest, const ndn::Data &data)
{
    auto sendTimeIt = m_sentInterests.find(interest.getName());

    if (sendTimeIt == m_sentInterests.end())
    {
        std::cerr << "Received Data for unknown Interest " << interest.getName() << std::endl;
        return;
    }

    auto receiveTime = std::chrono::steady_clock::now();
    auto sendTime = sendTimeIt->second;

    // Calculate RTT
    auto rtt = std::chrono::duration_cast<std::chrono::milliseconds>(receiveTime - sendTime).count();

    m_sentInterests.erase(sendTimeIt);

    // TODO: Verify Data packet

    // Extract sender's name and reply code from the Data content
    ndn::Block content = data.getContent();
    content.parse();

    // Assuming content format: [Sender's Name TLV][Reply Code TLV]
    auto it = content.elements_begin();

    if (it == content.elements_end())
    {
        std::cerr << "Data content is empty or malformed" << std::endl;
        return;
    }

    // Extract Sender's Name
    ndn::Name senderName(*it);
    ++it;

    if (it == content.elements_end())
    {
        std::cerr << "Reply code is missing in Data content" << std::endl;
        return;
    }

    // Extract Reply Code
    // uint16_t replyCode = static_cast<uint16_t>(it->value_uint());
    uint16_t replyCode = static_cast<uint16_t>(ndn::readNonNegativeInteger(*it));

    // Display hop information
    std::cout << "Hop " << static_cast<int>(m_currentHopLimit - 1)
              << ", RTT: " << rtt << " ms"
              << ", Forwarder: " << senderName.toUri()
              << ", Reply Code: " << replyCode << std::endl;

    // Check if destination is reached
    if (replyCode == 1 || replyCode == 2 || replyCode == 3)
    {
        std::cout << "Destination reached. Traceroute completed." << std::endl;
        m_face.shutdown();
        return;
    }

    // Send Interest for the next hop
    sendTracerouteInterest();
}

void TracerouteClient::onTimeout(const ndn::Interest &interest)
{
    m_sentInterests.erase(interest.getName());

    std::cout << "Timeout for Interest with HopLimit: " << static_cast<int>(m_currentHopLimit - 1) << std::endl;

    // Send Interest for the next hop
    sendTracerouteInterest();
}

void TracerouteClient::onNack(const ndn::Interest &interest, const ndn::lp::Nack &nack)
{
    m_sentInterests.erase(interest.getName());

    std::cerr << "Received Nack for Interest " << interest.getName()
              << " with reason " << nack.getReason() << std::endl;

    // Optionally, decide how to handle the Nack
    sendTracerouteInterest();
}

int main(int argc, char **argv)
{
    if (argc < 2)
    {
        std::cerr << "Usage: traceroute-client <target-name> [max-hop-limit]" << std::endl;
        return 1;
    }

    ndn::Name targetName(argv[1]);
    uint8_t maxHopLimit = 30; // Default maximum HopLimit

    if (argc >= 3)
    {
        try
        {
            int maxHopLimitInput = std::stoi(argv[2]);

            // Validate maximum HopLimit
            if (maxHopLimit < 1 || maxHopLimit > 255)
            {
                throw std::invalid_argument("Must be between 1 and 255");
            }

            maxHopLimit = static_cast<uint8_t>(maxHopLimitInput);
        }
        catch (const std::invalid_argument &e)
        {
            std::cerr << "Invalid maximum HopLimit: " << argv[2] << std::endl;
            return 1;
        }
    }

    // Start the TracerouteClient with the specified target name and maximum HopLimit
    try
    {
        TracerouteClient client(targetName, maxHopLimit);
        client.run();
    }
    catch (const std::exception &e)
    {
        std::cerr << "ERROR: " << e.what() << std::endl;
        return 1;
    }

    return 0;
}