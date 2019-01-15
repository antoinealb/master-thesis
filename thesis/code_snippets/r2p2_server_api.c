void echo(long handle,
          struct iovec* iov,
          int iovcnt)
{
  struct iovec local_iov[1];
  memcpy(local_iov[0].iov_base, iov[0].iov_base);
  local_iov[0].iov_len = iov[0].iov_len;
  r2p2_send_response(handle, local_iov, 1);
}

/* ... */

r2p2_set_recv_cb(echo);
