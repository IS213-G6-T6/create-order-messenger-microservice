# create-order-messenger-microservice


example input:
const data = {
          "customerID": "10",
          "customer_name": "q",
          "phone_no": "9420000",
          "total_price": "100.00",
          "status": "testing",
          "order_items": [
            {
              "item_name": "rice",
              "itemID": 9,
              "quantity": 100
            },
            {
              "item_name": "fish",
              "itemID": 10,
              "quantity": 200
            }
          ]
        };

        axios.post('http://localhost:5100/placeOrder', data)
          .then(response => {
            console.log(response.data)
            window.open(response.data.url)
          })
          .catch(error => {
            //console.error(error);
          });

