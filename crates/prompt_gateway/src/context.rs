use std::str::FromStr;

use common::errors::ServerError;
use common::stats::IncrementingMetric;
use http::StatusCode;
use log::warn;
use proxy_wasm::traits::Context;

use crate::stream_context::{ResponseHandlerType, StreamContext};

impl Context for StreamContext {
    fn on_http_call_response(
        &mut self,
        token_id: u32,
        _num_headers: usize,
        body_size: usize,
        _num_trailers: usize,
    ) {
        let callout_context = self
            .callouts
            .get_mut()
            .remove(&token_id)
            .expect("invalid token_id");
        self.metrics.active_http_calls.increment(-1);

        let body = self
            .get_http_call_response_body(0, body_size)
            .unwrap_or_default();

        if let Some(http_status) = self.get_http_call_response_header(":status") {
            match StatusCode::from_str(http_status.as_str()) {
                Ok(status_code) => {
                    if !status_code.is_success() {
                        let server_error = ServerError::Upstream {
                            host: callout_context.upstream_cluster.unwrap(),
                            path: callout_context.upstream_cluster_path.unwrap(),
                            status: http_status.clone(),
                            body: String::from_utf8(body).unwrap(),
                        };
                        warn!("received non 2xx code: {:?}", server_error);
                        return self.send_server_error(
                            server_error,
                            Some(StatusCode::from_str(http_status.as_str()).unwrap()),
                        );
                    }
                }
                Err(_) => {
                    // invalid status code (status code non numeric)
                    return self.send_server_error(
                        ServerError::LogicError(format!("invalid status code: {}", http_status)),
                        Some(StatusCode::from_str(http_status.as_str()).unwrap()),
                    );
                }
            }
        } else {
            // :status header not found
            warn!("missing :status header");
        }

        #[cfg_attr(any(), rustfmt::skip)]
        match callout_context.response_handler_type {
            ResponseHandlerType::ArchFC => self.arch_fc_response_handler(body, callout_context),
            ResponseHandlerType::FunctionCall => self.api_call_response_handler(body, callout_context),
            ResponseHandlerType::DefaultTarget =>self.default_target_handler(body, callout_context),
        }
    }
}
