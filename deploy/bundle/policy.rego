package control_tower

default tool_grant := false
default rate_limit := false
default egress_allowlist := false
default model_naming := false

tool_grant if input.granted == true

rate_limit if {
    is_number(input.calls)
    is_number(input.limit)
    input.calls <= input.limit
}

egress_allowlist if input.allowed == true

model_naming if input.forbidden == false
