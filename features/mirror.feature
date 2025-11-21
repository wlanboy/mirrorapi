Feature: Mirror API
  The Mirror API should store and return mirrored request/response pairs for all HTTP methods.

  Scenario Outline: Save and lookup a mirror pair for <method>
    Given the API is running
    When I send a POST request to "/mirror/save" with body:
      """
      {
        "request": {"request_data": {"test": "<method>"}},
        "response": {"response_data": {"msg": "Hello <method>"}, "response_status": 200}
      }
      """
    Then the response status code should be 201
    And the response JSON should contain "message" = "Request/Response pair saved."

    When I send a <method> request to "/mirror/" with body:
      """
      {"test": "<method>"}
      """
    Then the response status code should be 200
    And the response JSON should contain "msg" = "Hello <method>"

    Examples:
      | method  |
      | GET     |
      | POST    |
      | PUT     |
      | DELETE  |
      | PATCH   |
