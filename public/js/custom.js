/**
 * Clientside helper functions
 */

const amounts = document.getElementsByClassName("amount");
for (let i = 0; i < amounts.length; i++) {
  amounts[i].textContent = (amounts[i].dataset.amount / 100).toFixed(2);
}

const form = document.querySelector("#payment-form");

if (form) {
  const stripe = Stripe(form.dataset.publishableKey);

  let elements;

  initialize();
  form.addEventListener("submit", handleSubmit);
  
  // Fetches a payment intent and captures the client secret
  async function initialize() {
    const item = new URLSearchParams(window.location.search).get("item");
    const response = await fetch("/create-payment-intent", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ item }),
    });
    const { clientSecret } = await response.json();

    const appearance = { theme: "stripe" };
    elements = stripe.elements({ appearance, clientSecret});

    const paymentElement = elements.create("payment", { layout: "accordion", wallets: { link: "never" } });
    paymentElement.mount("#payment-element");
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setLoading(true);

    const { error } = await stripe.confirmPayment({
      elements,
      confirmParams: {
      // Make sure to change this to your payment completion page
        return_url: window.location.origin + "/success",
      // Allow Stripe to send a receipt to the customer
        receipt_email: document.getElementById("email").value,
      },
    });
    // This point will only be reached if there is an immediate error when
    // confirming the payment. Otherwise, your customer will be redirected to
    // your `return_url`. For some payment methods like iDEAL, your customer will
    // be redirected to an intermediate site first to authorize the payment, then
    // redirected to the `return_url`.
    if (error.type === "card_error" || error.type === "validation_error") {
      showMessage(error.message);
    } else {
      showMessage("An unexpected error occurred.");
    }

    setLoading(false);
  }

  // ------- UI helpers -------
  function showMessage(messageText) {
    const messageContainer = document.querySelector("#payment-message");
    messageContainer.classList.remove("hidden");
    messageContainer.textContent = messageText;

    setTimeout(function () {
      messageContainer.classList.add("hidden");
      messageContainer.textContent = "";
    }, 4000);
  }

  function setLoading(isLoading) {
    if (isLoading) {
      document.querySelector("#submit").disabled = true;
      document.querySelector("#spinner").classList.remove("hidden");
      document.querySelector("#button-text").classList.add("hidden");
    } else {
      document.querySelector("#submit").disabled = false;
      document.querySelector("#spinner").classList.add("hidden");
      document.querySelector("#button-text").classList.remove("hidden");
    }
  }
}
