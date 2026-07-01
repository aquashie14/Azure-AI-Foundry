"""
Sample customer emails for testing the triage assistant.

Updated to match the Streamlit UI format:
- ET-XXXX IDs matching the inbox queue
- sender, time, priority fields for the queue display
- Realistic logistics company emails
- Edge cases included per D5 acceptance criteria
"""

SAMPLE_EMAILS = [
    {
        "id": "ET-1042",
        "sender": "Priya Shah",
        "time": "09:14",
        "subject": "Pallet delivery still not arrived",
        "priority": "High",
        "body": (
            "Hello, our pallet consignment TSK447812 was due at our Birmingham depot "
            "yesterday. The tracking has not moved since Hinckley and we need this stock "
            "for today's outbound run. Can someone confirm when it will arrive?"
        ),
    },
    {
        "id": "ET-1043",
        "sender": "Mark Ellison",
        "time": "09:22",
        "subject": "Need to change delivery address",
        "priority": "Normal",
        "body": (
            "Hi, I need to update the delivery address for order TSK448001. "
            "Please change it to Unit 4, Parkway Industrial Estate, Coventry, CV6 5NX. "
            "The order hasn't shipped yet so hopefully this is still possible."
        ),
    },
    {
        "id": "ET-1044",
        "sender": "Hannah Cooper",
        "time": "09:31",
        "subject": "Invoice query",
        "priority": "Normal",
        "body": (
            "Good morning, I've received invoice INV-20241109 but the amount doesn't "
            "match our purchase order PO-88234. The invoice shows £4,320 but our PO "
            "was agreed at £3,980. Could you clarify the difference? "
            "Happy to send over the PO if needed."
        ),
    },
    {
        "id": "ET-1045",
        "sender": "Owen Matthews",
        "time": "09:43",
        "subject": "Damaged cartons on delivery",
        "priority": "High",
        "body": (
            "Three cartons on delivery note DN-556123 arrived with significant crush "
            "damage this morning. The contents appear to be affected — two units are "
            "visibly broken. I've taken photos. Please advise on the claims process "
            "and whether you need the items returned before processing."
        ),
    },
    {
        "id": "ET-1046",
        "sender": "Claire Hodgson",
        "time": "09:51",
        "subject": "Still no delivery - third time contacting you",
        "priority": "High",
        "body": (
            "This is the third time I am emailing about order TSK446200. It was due "
            "10 days ago and nobody has given me a straight answer. I am absolutely "
            "furious and if this isn't resolved today I will be escalating to your "
            "management and leaving a formal complaint. I want a refund NOW."
        ),
    },
    {
        "id": "ET-1047",
        "sender": "James Okafor",
        "time": "10:02",
        "subject": "What is your returns process?",
        "priority": "Normal",
        "body": (
            "Hi there, I received my delivery last week but I've changed my mind "
            "about the order. Can you tell me what your returns process is and "
            "how long refunds typically take? The order reference is TSK445890."
        ),
    },
    {
        "id": "ET-1048",
        "sender": "Unknown",
        "time": "10:11",
        "subject": "Re: Re: Re: FWD: your invoice",
        "priority": "Normal",
        "body": (
            "asdkj see attached thx??? also when delivery. "
            "plz respond asap need answer today this is urgent!!!"
        ),
    },
    {
        "id": "ET-1049",
        "sender": "Sarah Brennan",
        "time": "10:15",
        "subject": "Address change AND missing delivery",
        "priority": "High",
        "body": (
            "Two things: first, I need to update my address to 8 Park Lane, "
            "Leeds, LS1 4DT for order TSK448200 which hasn't shipped yet. "
            "Second, my previous order TSK447100 still hasn't arrived and "
            "it's been 10 days — the tracking just shows 'in transit'."
        ),
    },
    {
        "id": "ET-1050",
        "sender": "Unknown",
        "time": "10:22",
        "subject": "",
        "priority": "Normal",
        "body": "hello is anyone there",
    },
]
