/* Function types used for the various
 * callbacks */
typedef void (*success_cb_f)(
  long handle,
  void* arg,
  struct iovec* iov,
  int iovcnt);

/* Sending a request */
struct r2p2_ctx ctx = {0};
ctx.routing_policy = FIXED_ROUTE;
ctx.destination = /* snip */;

struct iovec local_iov;
local_iov.iov_base = msg;
local_iov.iov_len = strlen(msg) + 1;

ctx.success_cb = success_cb;
ctx.arg = &some_state;
r2p2_send_req(&local_iov, 1, &ctx);
