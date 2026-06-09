import stripe
import os
import json
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv

load_dotenv()
# Don't put any keys in code. Use an environment variable (as shown
# here) or secrets vault to supply keys to your integration.
# See https://docs.stripe.com/keys-best-practices
client = stripe.StripeClient(os.getenv("STRIPE_SECRET_KEY"))

app = Flask(
    __name__,
    static_url_path="",
    template_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), "views"),
    static_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), "public"),
)

# Just hardcoding amounts here to avoid using a database
ITEMS = {
    "1": {"title": "The Art of Doing Science and Engineering", "amount": 2300},
    "2": {
        "title": "The Making of Prince of Persia: Journals 1985-1993",
        "amount": 2500,
    },
    "3": {
        "title": "Working in Public: The Making and Maintenance of Open Source",
        "amount": 2800,
    },
}


# Look up an item's title/amount by ID, returning an error message if not found
def get_item_data(item_id):
    item_data = ITEMS.get(item_id)
    if item_data:
        return item_data["title"], item_data["amount"], None
    return None, None, "No item selected"


# Home route
@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


# Checkout route
@app.route("/checkout", methods=["GET"])
def checkout():
    # Just hardcoding amounts here to avoid using a database
    item = request.args.get("item")
    title = None
    amount = None
    error = None

    # Fetch item data based on the item ID from the query parameter
    title, amount, error = get_item_data(item)
    if error:
        return jsonify({"error": error}), 400  # bad/missing item id

    return render_template(
        "checkout.html",
        publishable_key=os.getenv("STRIPE_PUBLISHABLE_KEY"),
        title=title,
        amount=amount,
        error=error,
    )


# Create Payment Intent route
@app.route("/create-payment-intent", methods=["POST"])
def create_payment():
    data = json.loads(request.data)
    item = data.get("item")
    title = None
    amount = None
    error = None

    # Fetch item data based on the item ID from the query parameter
    title, amount, error = get_item_data(item)
    if error:
        return jsonify({"error": error}), 400  # bad/missing item id

    # Create a PaymentIntent with the order amount and currency
    if item and amount:
        try:
            intent = client.v1.payment_intents.create(
                {
                    "amount": amount,
                    "currency": "sgd",
                    "description": f"Purchase of {title}",
                }
            )
            return jsonify({"clientSecret": intent.client_secret})
        except stripe.StripeError as e:
            error = str(e.user_message)
            return jsonify(error), 400


# Success route
@app.route("/success", methods=["GET"])
def success():
    payment_intent_id = request.values.get("payment_intent")
    if not payment_intent_id:
        return render_template("error.html", error="No payment intent ID provided")
    try:
        intent = client.v1.payment_intents.retrieve(payment_intent_id)
        description = intent.description
    except stripe.StripeError as e:
        return render_template("error.html", error=str(e.user_message))

    if intent.status == "succeeded":
        charge = client.v1.charges.retrieve(intent.latest_charge)
        return render_template(
            "success.html",
            currency=charge.currency.upper(),
            amount=intent.amount / 100,
            email=charge.receipt_email,
            chargeId=charge.id,
            payment_intent_id=payment_intent_id,
            description=description,
        )
    else:
        return render_template("error.html", error="Payment did not succeed")


if __name__ == "__main__":
    app.run(port=5000, host="0.0.0.0", debug=True)
