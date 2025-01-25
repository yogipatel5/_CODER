Vault has this stored [env]/nginxproxy endpoint.
yp@Yogis-Mac-Studio ~ % curl -X POST \
 -H "Content-Type: application/json" \
 -d '{"identity": "[IDENTITY]", "secret": "[SECRET]"}' \
 [ENDPOINT]/api/tokens
