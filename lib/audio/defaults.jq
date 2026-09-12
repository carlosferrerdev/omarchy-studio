# Default routing policy is not a statement about an application's actual route.
def clean_label:
  if type == "string" and length > 0 then gsub("[\u0000-\u001f\u007f]"; " ") else null end;
def default_endpoint($dump; $reachable; $key; $classes; $fallback):
  {status:"unavailable",reason:"probe_unavailable",node_id:null,name:null,state:null,kind:null,device_id:null} as $empty
  | [$dump[] | select(.type == "PipeWire:Interface:Metadata" and .props["metadata.name"] == "default")] as $metadata
  | [$metadata[].metadata[]? | select(.subject == 0 and .key == $key)] as $entries
  | if $reachable != true then $empty
    elif ($metadata | length) != 1 then $empty + {reason:"metadata_unavailable"}
    elif ($entries | length) == 0 then $empty + {status:"not_selected",reason:"no_default"}
    elif ($entries | length) != 1 then $empty + {reason:"ambiguous_default"}
    else
      ($entries[0].value | if type == "string" then (try fromjson catch null) else . end) as $value
      | if ($value | type) != "object" or ($value.name | type) != "string" or ($value.name | length) == 0
        then $empty + {reason:"malformed_default"}
        else
          [$dump[] | select(.type == "PipeWire:Interface:Node" and .info.props["node.name"] == $value.name)
            | select(.info.props["media.class"] as $class | $classes | index($class))] as $nodes
          | if ($nodes | length) == 0 then $empty + {reason:"node_not_found"}
            elif ($nodes | length) != 1 then $empty + {reason:"ambiguous_node"}
            else $nodes[0] as $node | $node.info.props as $props
              | ((try ($props["device.id"] | tonumber | select(. >= 0 and floor == .)) catch null) // null) as $device_id
              | [$dump[] | select(.type == "PipeWire:Interface:Device" and .id == $device_id and .info.props["media.class"] == "Audio/Device")] as $devices
              | {status:"selected",reason:"resolved",node_id:$node.id,
                 name:(($props["node.description"] | clean_label) // ($props["node.nick"] | clean_label) // $fallback),
                 state:(if (["running","idle","suspended","creating","error"] | index($node.info.state)) != null then $node.info.state else "unknown" end),
                 kind:(if $props["device.class"] == "monitor" then "monitor"
                   elif $props["node.virtual"] == true or $props["node.virtual"] == "true" or ($props["media.class"] | endswith("/Virtual")) then "virtual"
                   elif ($devices | length) == 1 then "device" else "unknown" end),
                 device_id:(if ($devices | length) == 1 then $device_id else null end)}
            end
        end
    end;
def default_devices($dump; $reachable):
  {source:"pw-dump default metadata",scope:"session_defaults",
   output:default_endpoint($dump; $reachable; "default.audio.sink"; ["Audio/Sink","Audio/Sink/Virtual"]; "Selected output"),
   input:default_endpoint($dump; $reachable; "default.audio.source"; ["Audio/Source","Audio/Source/Virtual"]; "Selected input")};
