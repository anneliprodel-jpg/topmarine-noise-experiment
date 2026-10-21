import streamlit as st

st.set_page_config(
    page_title="Top Marine Noise Experiment",
    page_icon="⚓",
    layout="wide"
)

st.title("Top Marine Noise Experiment")
st.caption("Same customer request. Different decisions.")

st.divider()

st.header("Customer request")

st.info(
    """
Hi,

I am looking for a floating pontoon to extend an existing fixed pier.
The pontoon would mainly be used for mooring one leisure boat with booms.

I am considering a T-shaped solution with a relatively long gangway,
because the existing fixed pier is approximately 1 metre above the water level.

The location is shallow and well sheltered from waves,
although strong northerly winds can occur.

I am thinking of a floating section of around 8 × 2 m,
but I am open to your recommendation.

Would additional flotation be needed near the booms?

Best regards
"""
)

st.divider()

st.header("Prepare your offer")

with st.form("dealer_offer"):

    dealer = st.text_input(
        "Dealer / Country",
        placeholder="Example: Finland"
    )

    pontoon_solution = st.text_input(
        "Recommended pontoon solution",
        placeholder="Example: SP, BP, LDP, MDP..."
    )

    pontoon_dimensions = st.text_input(
        "Pontoon dimensions",
        placeholder="Example: 2.4 × 9 m"
    )

    gangway = st.text_input(
        "Gangway + dimensions",
        placeholder="Example: aluminium gangway 1.2 × 6 m"
    )

    booms = st.text_input(
        "Booms",
        placeholder="Type, quantity and dimensions"
    )

    anchoring = st.text_area(
        "Anchoring solution",
        placeholder="Describe the anchoring solution you would offer"
    )

    other_equipment = st.text_area(
        "Other equipment you consider necessary",
        placeholder="Ladder, cleats, fenders, additional floats, etc."
    )

    total_price = st.number_input(
        "Total price, EUR excl. VAT",
        min_value=0.0,
        step=100.0,
        format="%.2f"
    )

    predicted_difference = st.slider(
        "How different do you think the lowest and highest total offers will be?",
        min_value=0,
        max_value=200,
        value=25,
        step=5,
        format="%d%%"
    )

    submitted = st.form_submit_button(
        "Submit offer",
        use_container_width=True
    )

if submitted:
    st.success("Offer submitted.")

    st.subheader("Your offer summary")

    col1, col2 = st.columns(2)

    with col1:
        st.write("**Dealer / Country:**", dealer)
        st.write("**Recommended pontoon solution:**", pontoon_solution)
        st.write("**Pontoon dimensions:**", pontoon_dimensions)
        st.write("**Gangway:**", gangway)
        st.write("**Booms:**", booms)

    with col2:
        st.write("**Anchoring solution:**", anchoring)
        st.write("**Other equipment:**", other_equipment)
        st.write(f"**Total price:** €{total_price:,.2f}")
        st.write(
            f"**Expected difference between lowest and highest offer:** "
            f"{predicted_difference}%"
        )

    st.warning(
        "Do not discuss your offer with the other dealers before the results are revealed."
    )
