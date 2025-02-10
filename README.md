# Cleaner OneDrive

This project is designed to help you clean up your OneDrive files using Microsoft Graph API.

## Prerequisites

- Python 3.13 or higher
- An Azure personal account
- Microsoft Graph API permissions
- [Poetry](https://python-poetry.org/) for dependency management

## Getting Started

### Step 1: Register an Application in Azure

1. Go to the [Azure Portal](https://portal.azure.com/).
2. Navigate to **Azure Active Directory** > **App registrations** > **New registration**.
3. Enter a name for your application.
4. Set the **Supported account types** to **Accounts in any organizational directory and personal Microsoft accounts**.
5. Click **Register**.

### Step 2: Configure API Permissions

1. In the app registration page, go to **API permissions** > **Add a permission**.
2. Select **Microsoft Graph**.
3. Choose **Delegated permissions** and add the following permissions:
    - `Files.ReadWrite.All`
    - `User.Read`
4. Click **Add permissions**

### Step 3: Manifest

1. Make share that signInAudience in the manifest has the right value:
   - Go to the [Azure Portal](https://portal.azure.com).
   - In the left menu, select **Azure Active Directory**.
   - Go to **App registrations**.
   - Select the application you registered for authentication.
   - In the left menu, under **Manage**, click on **Manifest**.
   - You will see a JSON file containing the application configuration. You need to modify if needed the `signInAudience` property to allow authentication for users with personal Microsoft accounts.
4. Make sure that `"signInAudience": "AzureADandPersonalMicrosoftAccount"`.
5. Make sure to read this for future changes of the manifest format: [Manifest Deprecation](https://learn.microsoft.com/en-us/entra/identity-platform/azure-active-directory-graph-app-manifest-deprecation).

## Configuration

Set the following environment variables in your system:

```bash
export CLIENT_ID="YOUR_CLIENT_ID"
export TENANT_ID="YOUR_TENANT_ID"
export CLIENT_SECRET="YOUR_CLIENT_SECRET"
```

Alternatively, you can create a .env file in the root directory of your project with the following content (alue):

```env
CLIENT_ID=YOUR_CLIENT_ID
TENANT_ID=YOUR_TENANT_ID
CLIENT_SECRET=YOUR_CLIENT_SECRET
```

## Poetry Setup

### Step 1: Install Poetry

Follow the instructions on the [Poetry website](https://python-poetry.org/docs/#installation) to install Poetry.

### Step 2: Install Dependencies

Navigate to the project directory and run:

```bash
poetry install
```

### Step 3: Run the Project

Use Poetry to run the script:

```bash
poetry run python main.py
```

## Getting a Token

The script will use the provided `client_id`, `tenant_id`, and `client_secret` to obtain an access token from Microsoft Graph API.

## Running the Script

The script performs the following tasks:
1. Fetches an access token using MSAL.
2. Scans OneDrive folders iteratively to avoid deep recursion.
3. Detects duplicate files based on size and quickXorHash using Polars.
4. Prompts the user to delete duplicate files.

To run the script for test, use:

```bash
poetry run python main.py
```
or 
```bash
poetry run python3 ./cleaner_onedrive/main.py
``` 
depending on where you are what config , 

## Testing

```bash
poetry run pytest --cov=cleaner_onedrive -v --capture=no
```

## Contributing

Feel free to submit issues or pull requests if you have any improvements or bug fixes.

## License

This project is licensed under the MIT License.