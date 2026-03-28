# HTTP, APIs, CORS, and API Security — Research Summary

## 1. Basic Functionality of HTTP

HTTP (Hypertext Transfer Protocol) is the foundational communication protocol used on the web. It defines how clients and servers exchange messages over a network, typically the internet. HTTP operates using a request–response model, meaning one system asks for information and another sends it back.

### Clients

A client is any system that sends HTTP requests.

Common examples:

- Web browsers (Chrome, Edge, Safari)
- Mobile apps
- Desktop applications
- Scripts or services (e.g., Python programs using requests)

The client initiates communication by sending a request to a server.

Example client actions:

- Loading a webpage
- Submitting a form
- Fetching data from an API
- Uploading files

### Servers

A server is a system that listens for requests and responds with resources.

Servers host:

- Websites
- APIs
- Files
- Databases (indirectly through applications)

Examples:

- Web servers like Apache, Nginx
- Application servers using Flask, FastAPI, or Node.js

A server processes incoming requests and returns responses containing data or confirmation messages.

### Requests

An HTTP request is sent from a client to a server asking for a resource or action.

A request contains:

- **Request line** — includes HTTP method, URL, and protocol version
- **Headers**
- **Body** (optional)

Example:

```
GET /users HTTP/1.1
```

### Responses

An HTTP response is sent from the server back to the client.

It includes:

- **Status line**
- **Headers**
- **Body**

Example:

```
HTTP/1.1 200 OK
Content-Type: application/json
```

The response body usually contains:

- HTML (webpages)
- JSON (API data)
- Images
- Files

### Headers vs. Body

#### Headers

Headers contain metadata about the request or response.

Common examples:

- `Content-Type` — format of data (JSON, HTML, etc.)
- `Authorization` — security credentials
- `User-Agent` — identifies the client
- `Accept` — specifies response formats

Headers help control behavior and communication.

#### Body

The body contains the actual data being transmitted.

Examples:

- JSON data in API calls
- Form submissions
- File uploads
- HTML page content

Example JSON body:

```json
{
  "name": "John",
  "email": "john@example.com"
}
```

### Status Codes

HTTP status codes indicate whether a request succeeded or failed.

| Range | Meaning |
|---|---|
| 1xx | Informational |
| 2xx | Success |
| 3xx | Redirection |
| 4xx | Client error |
| 5xx | Server error |

Common examples:

| Code | Meaning |
|---|---|
| 200 OK | Request succeeded |
| 201 Created | Resource created |
| 400 Bad Request | Invalid request |
| 401 Unauthorized | Authentication required |
| 403 Forbidden | Access denied |
| 404 Not Found | Resource not found |
| 500 Internal Server Error | Server failure |

### HTTP Verbs (Methods)

HTTP verbs define the type of action being performed.

#### GET

Used to retrieve data.

```
GET /users
```

Characteristics:

- Does not modify data
- Safe and idempotent

#### POST

Used to create new resources.

```
POST /users
```

Characteristics:

- Sends data to the server
- Often creates records

#### PUT

Used to update or replace resources.

```
PUT /users/123
```

Characteristics:

- Updates existing data
- Idempotent

#### DELETE

Used to remove resources.

```
DELETE /users/123
```

Characteristics:

- Deletes data
- Idempotent

### Why HTTP is Stateless

HTTP is described as stateless because each request is treated as independent and contains all the information needed to process it.

This means:

- The server does not remember previous requests
- Every request must include necessary data
- No session memory exists by default

#### What Stateless Means in Practice

Example: if a user logs in, the server does not automatically remember them — the client must send authentication info with each request.

Common solutions:

- Cookies
- Session IDs
- Tokens (JWT)

Statelessness improves scalability, reliability, and load balancing because any server can handle any request.

---

## 2. The Role of APIs in Modern Applications

An API (Application Programming Interface) allows different software systems to communicate with each other.

Modern applications rely heavily on APIs to:

- Access data
- Integrate services
- Enable modular architectures
- Support mobile and web apps

Example: a mobile weather app calls an API to retrieve temperature data instead of storing weather data locally.

### What Are Open APIs?

Open APIs (also called public APIs) are APIs made available to external developers.

Characteristics:

- Publicly accessible
- Well-documented
- Often require authentication keys
- Enable third-party integrations

### Why Open APIs Are Important

Open APIs:

- Encourage innovation
- Enable ecosystem growth
- Allow integration between systems
- Reduce development time
- Support third-party applications

Examples: payment systems, social media integrations, mapping services.

### Example: Google Maps API (Modern Open API Use)

One widely used Open API is the Google Maps API.

How it is used:

- Businesses embed maps into websites
- Ride-sharing apps calculate routes
- Delivery systems track vehicles
- Real estate sites display property locations

Typical workflow:

1. Application requests map data
2. Google Maps API processes the request
3. Map data is returned
4. Application displays location visually

Example usage:

- Uber uses mapping APIs to route drivers
- Restaurants display location maps
- Logistics companies optimize deliveries

### Sources

Google Developers. (2024). *Google Maps Platform Documentation*. https://developers.google.com/maps

Fielding, R. (2000). *Architectural Styles and the Design of Network-Based Software Architectures* (REST Dissertation). https://www.ics.uci.edu/~fielding/pubs/dissertation/top.htm

Mozilla Developer Network (MDN). (2024). *HTTP Overview*. https://developer.mozilla.org/en-US/docs/Web/HTTP/Overview

---

## 3. Cross-Origin Resource Sharing (CORS)

CORS (Cross-Origin Resource Sharing) is a browser security mechanism that controls how resources are shared across different origins.

An origin consists of:

- Protocol
- Domain
- Port

Example origins:

- `https://example.com`
- `https://api.example.com`
- `http://example.com:3000`

These are considered different origins.

### Why CORS Exists

Browsers enforce the Same-Origin Policy, which blocks requests between different origins by default. CORS allows exceptions safely.

### How CORS Works

Servers send special headers allowing access.

Common headers:

- `Access-Control-Allow-Origin`
- `Access-Control-Allow-Methods`
- `Access-Control-Allow-Headers`

Example:

```
Access-Control-Allow-Origin: https://example.com
```

This tells the browser that cross-origin requests are allowed.

### When CORS Is Used

Common scenarios:

- React frontend calling backend API
- Mobile apps requesting remote data
- External services consuming APIs

---

## 4. How APIs Are Secured

APIs must be secured to:

- Prevent unauthorized access
- Protect sensitive data
- Control usage

### Common API Security Methods

#### API Keys

A unique identifier used to authenticate requests.

Example:

```
GET /weather?apikey=123456
```

Used for tracking usage and basic authentication.

#### OAuth 2.0

A widely used authentication framework that allows secure login and third-party access without sharing passwords.

Example: "Login with Google"

#### JWT (JSON Web Tokens)

A token-based authentication method that includes encoded user identity, expiration time, and a digital signature.

Example:

```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### HTTPS (Encryption)

Secure APIs always use HTTPS, which protects credentials and data in transit. Encryption prevents interception attacks.

### Steps to Access a Secure API

Typical process:

1. Register for API access
2. Receive API credentials
3. Authenticate using API key or OAuth
4. Send authorized requests
5. Receive protected data

---

## 5. Five Public Open APIs for Data

### 1. OpenWeatherMap API

Provides current weather, forecasts, and climate data.

Website: https://openweathermap.org/api

Use cases: weather apps, travel planning, agriculture systems.

### 2. NASA Open API

Provides astronomy images, space data, and Mars rover photos.

Website: https://api.nasa.gov/

Use cases: education platforms, scientific research tools.

### 3. Google Maps API

Provides maps, directions, and location data.

Website: https://developers.google.com/maps

Use cases: navigation apps, delivery systems.

### 4. GitHub API

Provides repository data, user profiles, and commit history.

Website: https://docs.github.com/en/rest

Use cases: dev tools, CI/CD systems.

### 5. Spotify API

Provides music data, playlists, and artist information.

Website: https://developer.spotify.com/documentation/web-api/

Use cases: music apps, recommendation engines.

---

## Summary

HTTP forms the backbone of web communication through a stateless request–response model involving clients and servers. APIs extend this model by enabling systems to interact and share data efficiently. Open APIs promote innovation by allowing developers to build on shared platforms, while technologies like CORS and authentication mechanisms ensure secure and controlled data exchange. Together, these technologies define the foundation of modern web and cloud-based applications.
