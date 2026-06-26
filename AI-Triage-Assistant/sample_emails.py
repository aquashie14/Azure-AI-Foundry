"""
Sample customer emails for testing the triage assistant.
Per the brief: 5-10 realistic emails, including at least one
ambiguous or junk email to prove the assistant handles edge cases.
"""

SAMPLE_EMAILS = [
    {
        "id": "email-1",
        "subject": "Where is my parcel?",
        "body": (
            "Hi, I ordered a package last Tuesday and the tracking hasn't "
            "updated in 4 days. Order number is LX-22841. Can you tell me "
            "where it is?"
        ),
    },
    {
        "id": "email-2",
        "subject": "Need to update delivery address",
        "body": (
            "I just moved house and need to change the delivery address "
            "for an order that hasn't shipped yet. Order number LX-22990. "
            "New address: 14 Birch Road, Manchester, M14 5QT."
        ),
    },
    {
        "id": "email-3",
        "subject": "Damaged item - want to claim",
        "body": (
            "The box I received yesterday was crushed and the item inside "
            "(a ceramic vase) arrived broken. How do I file a claim and "
            "get a refund or replacement? Order LX-21750."
        ),
    },
    {
        "id": "email-4",
        "subject": "Still no delivery after 2 weeks",
        "body": (
            "This is the third email I'm sending. My order LX-22011 was "
            "supposed to arrive 2 weeks ago. I am extremely frustrated "
            "and want a refund if this isn't resolved today."
        ),
    },
    {
        "id": "email-5",
        "subject": "Question about claims process",
        "body": (
            "If an item arrives late and I no longer need it, can I "
            "return it for a full refund? What's the process and how "
            "long does it take?"
        ),
    },
    {
        "id": "email-6",
        "subject": "Re: Re: Re: FWD: your invoice",
        "body": (
            "asdkj see attached thx??? also when delivery. plz respond "
            "asap need answer today this is urgent!!!"
        ),
    },
    {
        "id": "email-7",
        "subject": "",
        "body": "hello is anyone there",
    },
    {
        "id": "email-8",
        "subject": "Address change AND delivery question",
        "body": (
            "Two things: first, I need to update my address to 8 Park "
            "Lane, Leeds, LS1 4DT for order LX-23010. Second, my previous "
            "order LX-22500 still hasn't arrived and it's been 10 days."
        ),
    },
]
