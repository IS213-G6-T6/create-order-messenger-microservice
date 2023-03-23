from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os, sys
import amqp_setup
import pika

import requests
from invokes import invoke_http

app = Flask(__name__)
CORS(app)

order_URL = "http://localhost:5000/order"
payment_URL = "http://localhost:5001/payment"
notification_URL = "http://localhost:5002/notification"
error_URL = "http://localhost:5003/error"
activity_log_URL = "http://localhost:5004/activity_log"


@app.route("/placeOrder", methods=['POST'])
def placeOrder():
    # Simple check of input format and data of the request are JSON
    if request.is_json:
        try:
            order = request.get_json()
            print("\nReceived an order in JSON:", order)

            # do the actual work
            # 1. Send order info {cart items}
            result = processPlaceOrder(order)
            return result

        except Exception as e:
            # Unexpected error in code
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            ex_str = str(e) + " at " + str(exc_type) + ": " + fname + ": line " + str(exc_tb.tb_lineno)
            print(ex_str)

            return jsonify({
                "code": 500,
                "message": "place_order.py internal error: " + ex_str
            }), 500

    # if reached here, not a JSON request.
    return jsonify({
        "code": 400,
        "message": "Invalid JSON input: " + str(request.get_data())
    }), 400

@app.route("/payment/success/<string:orderID>")
def successOrderPlace(orderID):
    return_result = invoke_http("http://localhost:5001/payment/success/" + orderID)
    get_order = json.dumps(invoke_http(order_URL + "/" + orderID))
    print(get_order)
    print(type(get_order))
    amqp_setup.channel.basic_publish(exchange=amqp_setup.exchangename, routing_key="neworder.notification", body=get_order, properties=pika.BasicProperties(delivery_mode = 2))

    return return_result

def processPlaceOrder(order):
    # 2. Send the order info {cart items}
    # Invoke the order microservice
    print('\n-----Invoking order microservice-----')
    order_result = invoke_http(order_URL, method='POST', json=order)
    print('order_result:', order_result)
    
    payment_json = {
                "name": order_result['data']['orderID'],
                "price": int(order_result['data']['total_price'] * 100),
                "quantity": 1,
                "orderID": str(order_result['data']['orderID'])
            }

    print(payment_json)
    # 4. Record new order
    # record the activity log anyway
    print('\n\n-----Invoking payment microservice-----')
    payment_result = invoke_http(payment_URL, method="POST", json=payment_json)
    print("\nOrder sent to payment.\n")
    # - reply from the invocation is not used;
    # continue even if this invocation fails
    print(payment_result)
    return payment_result

    # Check the order result; if a failure, send it to the error microservice.
    code = order_result["code"]
    if code not in range(200, 300):


    # Inform the error microservice
        print('\n\n-----Invoking error microservice as order fails-----')
        invoke_http(error_URL, method="POST", json=order_result)
            # - reply from the invocation is not used; 
            # continue even if this invocation fails
        print("Order status ({:d}) sent to the error microservice:".format(
            code), order_result)


    # 7. Return error
        return {
            "code": 500,
            "data": {"order_result": order_result},
            "message": "Order creation failure sent for error handling."
        }


    # # 5. Send new order to shipping
    # # Invoke the shipping record microservice
    # print('\n\n-----Invoking shipping_record microservice-----')
    # shipping_result = invoke_http(
    # shipping_record_URL, method="POST", json=order_result['data'])
    # print("shipping_result:", shipping_result, '\n')


    # # Check the shipping result;
    # # if a failure, send it to the error microservice.
    # code = shipping_result["code"]
    # if code not in range(200, 300):


    # # Inform the error microservice
    #     print('\n\n-----Invoking error microservice as shipping fails-----')
    #     invoke_http(error_URL, method="POST", json=shipping_result)
    #     print("Shipping status ({:d}) sent to the error microservice:".format(
    #         code), shipping_result)


    # # 7. Return error
    #     return {
    #         "code": 400,
    #         "data": {
    #             "order_result": order_result,
    #             "shipping_result": shipping_result
    #         },
    #         "message": "Simulated shipping record error sent for error handling."
    #     }


    # 7. Return created order, shipping record
    return {payment_result}


# Execute this program if it is run as a main script (not by 'import')
if __name__ == "__main__":
    print("This is flask " + os.path.basename(__file__) +
          " for placing an order...")
    app.run(host="0.0.0.0", port=5100, debug=True)
    # Notes for the parameters:
    # - debug=True will reload the program automatically if a change is detected;
    #   -- it in fact starts two instances of the same flask program,
    #       and uses one of the instances to monitor the program changes;
    # - host="0.0.0.0" allows the flask program to accept requests sent from any IP/host (in addition to localhost),
    #   -- i.e., it gives permissions to hosts with any IP to access the flask program,
    #   -- as long as the hosts can already reach the machine running the flask program along the network;
    #   -- it doesn't mean to use http://0.0.0.0 to access the flask program.
