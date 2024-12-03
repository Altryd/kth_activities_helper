package user

import (
	"encoding/json"
	"github.com/go-chi/chi/v5/middleware"
	"github.com/go-chi/render"
	"io"
	"kth_activities_helper/internal/config"
	resp "kth_activities_helper/internal/lib/response"
	"log/slog"
	"net/http"
	url2 "net/url"
	"strings"
)

type DiscordOAuthResponse struct {
	resp.Response
	Username  string `json:"username"`
	DiscordId string `json:"discord_id"`
}

func GetDiscordCode(log *slog.Logger) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		const op = "handlers.user.get.GetOne"
		localLog := log.With(
			slog.String("op", op),
			slog.String("request_id", middleware.GetReqID(r.Context())),
		)
		// PART 0: GETTING CODE
		var queryResults = r.URL.Query()
		if len(queryResults) != 1 {
			http.Error(w, http.StatusText(400), 400)
			return
		}
		var code = queryResults.Get("code")
		localLog.Info("Got code", slog.String("code", code))

		// PART 1: getting token
		var apiUrl = "https://discord.com"
		var resource = "/api/v10/oauth2/token"
		data := url2.Values{}
		data.Set("client_id", config.AppConfig.OAuthConfig.DiscordClientId)
		data.Set("client_secret", config.AppConfig.OAuthConfig.DiscordClientSecret)
		data.Set("grant_type", "authorization_code")
		data.Set("code", code)
		data.Set("redirect_uri", "http://localhost:8089/api/discord")

		u, _ := url2.ParseRequestURI(apiUrl)
		u.Path = resource
		urlStr := u.String()
		client := &http.Client{}
		req, err := http.NewRequest(http.MethodPost, urlStr, strings.NewReader(data.Encode()))
		if err != nil {
			localLog.Error("Something bad happened with post request")
			return
		}
		req.Header.Add("Content-Type", "application/x-www-form-urlencoded")
		response, err := client.Do(req)
		if err != nil {
			localLog.Error("Something bad happened with post request")
			http.Error(w, http.StatusText(500), 500)
			return
		}
		defer response.Body.Close()
		body, err := io.ReadAll(response.Body)
		var dataRead map[string]interface{}
		err = json.Unmarshal(body, &dataRead)
		if err != nil {
			return
		}
		if response.StatusCode != 200 {
			localLog.Error("Something bad when accessing ", slog.String(urlStr, "url"))
			http.Error(w, http.StatusText(500), 500)
			return
		}

		// PART2: GOT ACCESS TOKEN DISCORD, getting user info
		accessToken := dataRead["access_token"].(string)
		apiUrl = "https://discord.com"
		resource = "/api/v10/users/@me"

		u, _ = url2.ParseRequestURI(apiUrl)
		u.Path = resource
		urlStr = u.String()
		req, _ = http.NewRequest(http.MethodGet, urlStr, nil)
		req.Header.Add("Authorization", "Bearer "+accessToken)
		response, err = client.Do(req)
		if err != nil {
			localLog.Error("Something bad happened with GET request")
			http.Error(w, http.StatusText(500), 500)
			return
		}
		defer response.Body.Close()
		body, _ = io.ReadAll(response.Body)
		err = json.Unmarshal(body, &dataRead)
		if err != nil {
			http.Error(w, http.StatusText(500), 500)
			return
		}
		if response.StatusCode != 200 {
			localLog.Error("Something bad when accessing ", slog.String(urlStr, "url"))
			http.Error(w, http.StatusText(500), 500)
			return
		}
		id := dataRead["id"].(string)
		username := dataRead["username"].(string)

		render.JSON(w, r, DiscordOAuthResponse{ // TODO: придумать какой-то редирект наверное
			Response:  resp.OK(),
			DiscordId: id,
			Username:  username,
		})
		return
	}
}
