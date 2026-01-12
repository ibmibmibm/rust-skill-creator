# Rust Patterns for Skill Development

Common Rust patterns used in generated skills.

## HTTP Client with Reqwest

### Basic GET Request

```rust
use reqwest;

async fn fetch_data(url: &str) -> Result<String, reqwest::Error> {
    let response = reqwest::get(url).await?;
    let body = response.text().await?;
    Ok(body)
}
```

### GET Request with JSON Response

```rust
use reqwest;
use serde::Deserialize;

#[derive(Deserialize)]
struct ApiResponse {
    data: String,
    count: i32,
}

async fn fetch_json(url: &str) -> Result<ApiResponse, reqwest::Error> {
    let response = reqwest::get(url)
        .await?
        .json::<ApiResponse>()
        .await?;
    Ok(response)
}
```

### POST Request with JSON Body

```rust
use reqwest;
use serde::{Serialize, Deserialize};

#[derive(Serialize)]
struct RequestBody {
    query: String,
    limit: i32,
}

#[derive(Deserialize)]
struct ResponseData {
    results: Vec<String>,
}

async fn post_data(url: &str, body: RequestBody) -> Result<ResponseData, reqwest::Error> {
    let client = reqwest::Client::new();
    let response = client
        .post(url)
        .json(&body)
        .send()
        .await?
        .json::<ResponseData>()
        .await?;
    Ok(response)
}
```

### Request with Custom Headers

```rust
use reqwest::header::{HeaderMap, HeaderValue, AUTHORIZATION, CONTENT_TYPE};

async fn fetch_with_headers(url: &str, api_key: &str) -> Result<String, reqwest::Error> {
    let mut headers = HeaderMap::new();
    headers.insert(AUTHORIZATION, HeaderValue::from_str(&format!("Bearer {}", api_key)).unwrap());
    headers.insert(CONTENT_TYPE, HeaderValue::from_static("application/json"));

    let client = reqwest::Client::new();
    let response = client
        .get(url)
        .headers(headers)
        .send()
        .await?
        .text()
        .await?;
    Ok(response)
}
```

### Query Parameters

```rust
async fn fetch_with_params(base_url: &str, location: &str, key: &str) -> Result<String, reqwest::Error> {
    let client = reqwest::Client::new();
    let response = client
        .get(base_url)
        .query(&[("q", location), ("appid", key)])
        .send()
        .await?
        .text()
        .await?;
    Ok(response)
}
```

## JSON Parsing with Serde

### Basic Struct

```rust
use serde::{Deserialize, Serialize};

#[derive(Debug, Serialize, Deserialize)]
struct User {
    name: String,
    email: String,
    age: Option<i32>,
}
```

### Nested Structs

```rust
#[derive(Debug, Deserialize)]
struct Weather {
    location: Location,
    current: CurrentWeather,
}

#[derive(Debug, Deserialize)]
struct Location {
    name: String,
    country: String,
}

#[derive(Debug, Deserialize)]
struct CurrentWeather {
    temp_c: f64,
    condition: Condition,
}

#[derive(Debug, Deserialize)]
struct Condition {
    text: String,
}
```

### Rename Fields

```rust
use serde::{Deserialize, Serialize};

#[derive(Debug, Deserialize)]
struct ApiData {
    #[serde(rename = "firstName")]
    first_name: String,

    #[serde(rename = "lastName")]
    last_name: String,

    #[serde(rename = "createdAt")]
    created_at: String,
}
```

### Optional and Default Values

```rust
use serde::{Deserialize, Serialize};

#[derive(Debug, Deserialize)]
struct Config {
    name: String,

    #[serde(default)]
    enabled: bool,

    #[serde(default = "default_timeout")]
    timeout: u32,

    description: Option<String>,
}

fn default_timeout() -> u32 {
    30
}
```

### Parse and Serialize JSON

```rust
use serde_json;

// Parse JSON string to struct
let json_str = r#"{"name": "test", "value": 42}"#;
let data: MyStruct = serde_json::from_str(json_str)?;

// Serialize struct to JSON string
let output = serde_json::to_string(&data)?;
let pretty = serde_json::to_string_pretty(&data)?;
```

## CLI Argument Parsing

### Basic Arguments (without clap)

```rust
use std::env;

fn main() {
    let args: Vec<String> = env::args().collect();

    // args[0] is the program name
    // args[1] is the first argument

    let input = args.get(1).expect("Missing required argument");
    let optional = args.get(2).map(|s| s.as_str()).unwrap_or("default");

    println!("Input: {}, Optional: {}", input, optional);
}
```

### Parsing Typed Arguments

```rust
use std::env;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let args: Vec<String> = env::args().collect();

    let count: i32 = args.get(1)
        .ok_or("Missing count argument")?
        .parse()?;

    let enabled: bool = args.get(2)
        .map(|s| s == "true")
        .unwrap_or(false);

    println!("Count: {}, Enabled: {}", count, enabled);
    Ok(())
}
```

## Environment Variables

### Reading Environment Variables

```rust
use std::env;

fn get_api_key() -> Result<String, env::VarError> {
    env::var("API_KEY")
}

fn get_with_default(key: &str, default: &str) -> String {
    env::var(key).unwrap_or_else(|_| default.to_string())
}
```

## Error Handling Patterns

### Result Type

```rust
use std::error::Error;

async fn main() -> Result<(), Box<dyn Error>> {
    let result = some_operation()?;  // Propagate error with ?
    Ok(())
}
```

### Custom Error Messages

```rust
fn validate_input(input: &str) -> Result<(), String> {
    if input.is_empty() {
        return Err("Input cannot be empty".to_string());
    }
    Ok(())
}
```

### Error Context

```rust
use std::error::Error;

async fn fetch_user(id: i32) -> Result<User, Box<dyn Error>> {
    let url = format!("https://api.example.com/users/{}", id);
    let response = reqwest::get(&url)
        .await
        .map_err(|e| format!("Failed to fetch user {}: {}", id, e))?;

    if !response.status().is_success() {
        return Err(format!("API returned status: {}", response.status()).into());
    }

    let user = response.json::<User>()
        .await
        .map_err(|e| format!("Failed to parse user response: {}", e))?;

    Ok(user)
}
```

## Async Patterns with Tokio

### Async Main Function

```rust
#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    // Async code here
    Ok(())
}
```

### Concurrent Requests

```rust
use futures::future::join_all;

async fn fetch_multiple(urls: Vec<&str>) -> Vec<Result<String, reqwest::Error>> {
    let futures = urls.into_iter().map(|url| reqwest::get(url));
    let responses = join_all(futures).await;

    let mut results = Vec::new();
    for response in responses {
        match response {
            Ok(r) => results.push(r.text().await),
            Err(e) => results.push(Err(e)),
        }
    }
    results
}
```

## Output Formatting

### JSON Output

```rust
use serde::Serialize;
use serde_json;

#[derive(Serialize)]
struct Output {
    status: String,
    data: Vec<String>,
}

fn print_json_output(data: &Output) {
    println!("{}", serde_json::to_string_pretty(data).unwrap());
}
```

### Text Output

```rust
fn print_result(result: &str) {
    println!("{}", result);
}

fn print_error(msg: &str) {
    eprintln!("Error: {}", msg);
}
```
