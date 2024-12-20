#include <ndn-cxx/face.hpp>
#include <ndn-cxx/security/key-chain.hpp>
#include <ndn-cxx/encoding/block-helpers.hpp>
#include <iostream>

class SimpleProducer
{
public:
    SimpleProducer(char *name) : name(name) {}

    void run(char *data_name)
    {
        m_face.setInterestFilter(ndn::Name(data_name),
                                 std::bind(&SimpleProducer::onInterest, this, std::placeholders::_1, std::placeholders::_2),
                                 std::bind(&SimpleProducer::onRegisterSuccess, this, std::placeholders::_1),
                                 std::bind(&SimpleProducer::onRegisterFailed, this, std::placeholders::_1, std::placeholders::_2));

        std::cout << "SimpleProducer: Listening for Interests on " << data_name << std::endl;

        m_face.processEvents();
    }

private:
    void onInterest(const ndn::InterestFilter &filter, const ndn::Interest &interest)
    {
        std::cout << "Received Interest: " << interest.getName() << std::endl;

        // Create Data packet with the same name as the Interest
        ndn::Data data(interest.getName());

        // Set a freshness period
        data.setFreshnessPeriod(ndn::time::milliseconds(1000));

        // Create content
        ndn::Name senderName(this->name);
        uint16_t replyCode = 4; // No Error

        // Build content block
        ndn::Block content(ndn::tlv::Content);

        // Add sender's name
        ndn::Block senderNameBlock = senderName.wireEncode();
        content.push_back(senderNameBlock);

        // Add reply code
        ndn::Block replyCodeBlock = ndn::makeNonNegativeIntegerBlock(128, replyCode); // 128 is a custom TLV type
        content.push_back(replyCodeBlock);

        // Encode the content block
        content.encode();

        // Set content to data
        data.setContent(content);

        // Sign the Data packet
        m_keyChain.sign(data);

        // Send the Data packet
        m_face.put(data);
    }

    void onRegisterSuccess(const ndn::Name &prefix)
    {
        std::cout << "Successfully registered prefix: " << prefix << std::endl;
    }

    void onRegisterFailed(const ndn::Name &prefix, const std::string &reason)
    {
        std::cerr << "Failed to register prefix \"" << prefix << "\": " << reason << std::endl;
        m_face.shutdown();
    }

private:
    char *name;
    ndn::Face m_face;
    ndn::KeyChain m_keyChain;
};

int main(int argc, char *argv[])
{
    if (argc < 3)
    {
        std::cerr << "Usage: simple-producer <producer-name> <data-name>" << std::endl;
        return 1;
    }

    char *name = argv[1];
    char *data_name = argv[2];

    try
    {
        SimpleProducer producer(name);
        producer.run(data_name);
    }
    catch (const std::exception &e)
    {
        std::cerr << "ERROR: " << e.what() << std::endl;
    }
    return 0;
}
