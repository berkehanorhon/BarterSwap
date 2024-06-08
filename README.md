# BarterSwap Project

BarterSwap is an online platform that allows users to auction their items for trade. The project is written in Python, using the Flask web framework and Jinja templating engine. It uses a PostgreSQL database for data storage.

## Features

- **User Registration and Authentication**: Users can register and create an account. User passwords are securely hashed and stored. Users can log in to their account to access more features.

- **Item Listing**: Users can list their items for auction. Each item has a title, description, category, starting price, and an optional image.

- **Bidding**: Users can place bids on active auctions. The highest bid at the end of the auction wins. The system ensures that users have sufficient balance before placing a bid.

- **Messaging**: Users can send messages to each other. This can be used for discussing details about an auction or trade.

- **Transaction Processing**: The system automatically processes transactions when an auction ends. The highest bidder wins the item and their balance is updated accordingly.

- **Virtual Currency**: The system includes a virtual currency that users can use for bidding. Users can deposit real money into their account to get virtual currency.

- **Admin Panel**: Admins can manage users and auctions. They can ban users, stop auctions, and adjust users' balances.

## Configuration

The `settings.yaml` file is used to configure the application. Here is an example of how to fill it out:

```yaml
database:
    host: "your_database_host"
    port: your_database_port
    name: "your_database_name"
    user: "your_database_username"
    password: "your_database_password"
jwt:
    secret_key: "your_jwt_secret_key"
private_hash:
    password: "your_private_hash_password"

    
## Installation

1. Clone the project to your local machine:
    ```
    git clone https://github.com/yourusername/barterswap.git
    ```

2. Install the necessary dependencies:
    ```
    pip install -r requirements.txt
    ```

3. Start the database:
    ```
    python barterswap.py start_database
    ```

## Technologies Used

- Python: The main language used for the application.
- Flask: The web framework used for handling requests and routing.
- Jinja: The templating engine used for generating HTML responses.
- PostgreSQL: The database management system used for data storage.
- PyCharm: The IDE used for development.
