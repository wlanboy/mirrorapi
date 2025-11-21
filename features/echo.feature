Feature: Echo API
  The Echo endpoint should return headers and body as received,
  and respect statuscode, waittime and errorcode parameters.

  Scenario: Echo returns JSON body
    Given the API is running
    When I send a POST request to "/echo/statuscode/200" with body:
      """
      {"body": "Hallo Echo"}
      """
    Then the response status code should be 200
    And the response JSON should contain "received_body.body" = "Hallo Echo"

  Scenario: Echo returns custom status code from path
    Given the API is running
    When I send a GET request to "/echo/statuscode/201"
    Then the response status code should be 201

  Scenario: Echo returns error message from path
    Given the API is running
    When I send a GET request to "/echo/errorcode/kaputt"
    Then the response status code should be 500
    And the response JSON should contain "error" = "kaputt"

  Scenario: Echo returns status code from header
    Given the API is running
    When I send a GET request to "/echo/test" with header "request-statuscode" = "202"
    Then the response status code should be 202

  Scenario: Echo waits before responding
    Given the API is running
    When I send a GET request to "/echo/waittime/1"
    Then the response status code should be 200

  Scenario: Echo returns invalid header value
    Given the API is running
    When I send a GET request to "/echo/test" with header "request-statuscode" = "abc"
    Then the response status code should be 400
    And the response JSON should contain "error" = "Invalid value for request-statuscode, must be an integer."

  Scenario: Echo echoes back custom header
    Given the API is running
    When I send a GET request to "/echo/test" with header "X-Custom" = "foobar"
    Then the response status code should be 200
    And the response header "X-Custom" should equal "foobar"

  Scenario: Echo returns plain text body
    Given the API is running
    When I send a POST request to "/echo/statuscode/200" with raw body:
      """
      plain text body
      """
    Then the response status code should be 200
    And the response JSON should contain "received_body" = "plain text body"
