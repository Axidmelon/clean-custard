Excellent question. This is the most critical user interaction in the entire application, and our UI/UX must reflect our security-first architecture.

When a user clicks on the "Make a Supabase Connection" card, we **do not** show them a traditional form asking for their database host, username, and password. That would violate our core security principle.

Instead, we pop up a guided, two-step experience that teaches them how to run our secure agent.

---

### The User Experience Flow: Secure Connection Guide

When the user clicks the card, a modal window appears.

#### **Step 1: Name Your Connection**

The first screen of the modal is extremely simple.

**What the UI Shows (Output):**
*   **Title:** `Connect to Your Supabase Database`
*   **Input Field (What we get from the user):**
    *   **Label:** `Connection Name`
    *   **Placeholder:** `e.g., Production Analytics DB`
    *   **Help Text:** "This is a friendly name for your own reference."
*   **Button:** `[ Generate Connection Command ]`

This is the **only** piece of information we ask for upfront.



---

#### **Step 2: Run the Secure Connector Agent**

Once the user enters a name and clicks the button, the modal transitions to the second screen. This is where the magic happens.

**Behind the Scenes:** The frontend sends a `POST /api/v1/connections` request to our backend with the name. The backend creates a new connection record, generates a unique `CUSTARD_API_KEY` for the agent, and sends this key back to the frontend.

**What the UI Shows (Output):**
{
*   **Title:** `Step 2: Run the Secure Connector Agent`
*   **Explanation Text:** "For your security, our agent runs inside your network. This ensures your database credentials **never** leave your control. Copy the command below and run it in your server environment where it can access your database."

*   **The Generated Command (The core output):**
    A code block is displayed with the full `docker run` command, featuring a one-click "Copy" button. The `CUSTARD_API_KEY` is pre-filled. **Crucially, the user's secrets are shown as clear placeholders.**

    ```bash
    docker run -d \
      --name agent-postgresql-prod \
      -e CUSTARD_API_KEY="agent_key_abc123_is_prefilled_here" \
      -e CUSTOMER_DB_HOST="YOUR_SUPABASE_HOST" \
      -e CUSTOMER_DB_PORT="6543" \
      -e CUSTOMER_DB_USER="YOUR_READONLY_USER" \
      -e CUSTOMER_DB_PASSWORD="YOUR_DB_PASSWORD" \
      -e CUSTOMER_DB_NAME="postgres" \
      -e DB_SSLMODE="require" \
      custard/agent:latest
    ```

*   **Help Section:** A small, helpful section below the code block.
    *   **Title:** "Where to find these values in Supabase:"
    *   **Content:** "Log in to your Supabase dashboard, go to **Project Settings > Database**. Use the 'Connection Info' details. We strongly recommend creating a dedicated, `read-only` user for Custard."
    *   A hyperlink to the Supabase documentation can be included here.

*   **Live Status Indicator:**
    A live status indicator is displayed at the bottom of the modal.
    *   **Initial State:** `🟡 Waiting for connection...`
}


---

### The "Magic Moment": Connection Confirmation

1.  The user copies the command.
2.  They paste it into their own server's terminal, replacing the `YOUR_...` placeholders with their actual Supabase credentials.
3.  They run the command. The agent starts.
4.  The agent connects to our backend's WebSocket.
5.  Our backend detects the successful connection and notifies the frontend.

**The modal UI instantly and automatically updates:**

*   **Final State:** `✅ Connected! You can now close this window.`

The modal can then be closed, and on the main dashboard, the "Supabase" connection card now shows a small green light, indicating it's live and ready to be queried.

### Why This Approach Is Superior

*   **Security:** We never see, touch, or store their database password. The user experience reinforces this and builds immense trust.
*   **Clarity:** It's a guided, step-by-step process, not an intimidating form with a dozen fields.
*   **Empowerment:** It teaches the user exactly what is happening, giving them full control over the agent running in their environment.