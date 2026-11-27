FROM scratch AS runtime
ADD --checksum=sha256:24e344d1fc394cd93dc75666f584cfb97c6981f7255af25f8d2979834317317b --chmod=0555 https://github.com/open-policy-agent/opa/releases/download/v1.22.2/opa_linux_amd64_static /opa
COPY --chmod=0444 policy.rego /policy.rego
USER 10001:10001
EXPOSE 8181
HEALTHCHECK --interval=5s --timeout=3s CMD ["/opa", "eval", "--fail", "--format=raw", "http.send({\"method\":\"get\",\"url\":\"http://127.0.0.1:8181/health\"}).status_code == 200"]
ENTRYPOINT ["/opa"]
CMD ["run", "--server", "--addr=0.0.0.0:8181", "/policy.rego"]
