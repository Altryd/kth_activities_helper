package user

import (
	"encoding/json"
	"github.com/Altryd/osuParseMpLinks"
	"github.com/go-chi/chi/v5/middleware"
	"github.com/go-chi/render"
	"io"
	resp "kth_activities_helper/internal/lib/response"
	"log/slog"
	"net/http"
	url2 "net/url"
	"strconv"
	"strings"
)

type OsuOAuthResponse struct {
	resp.Response
	Username string `json:"username"`
	OsuId    int    `json:"osu_id"`
}

func GetOsuCode(log *slog.Logger) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		const op = "handlers.user.get.GetOne"
		localLog := log.With(
			slog.String("op", op),
			slog.String("request_id", middleware.GetReqID(r.Context())),
		)
		// PART 0: GETTING CODE
		var queryResults = r.URL.Query() // TODO : можно подумать над state, но как бы неважно пока что
		if len(queryResults) != 2 {
			http.Error(w, http.StatusText(400), 400) // TODO: redirect here
			return
		}
		var code = queryResults.Get("code")
		localLog.Info("Got code", slog.String("code", code))

		// PART 1: getting token

		var apiUrl = "https://osu.ppy.sh"
		var resource = "/oauth/token"
		data := url2.Values{}
		secretData, err := osuParseMpLinks.NewSecretData("internal/config/secrets.json")
		if err != nil {
			localLog.Error("Failed to get secret data")
			w.WriteHeader(http.StatusInternalServerError)
			http.Error(w, http.StatusText(500), 500)
			return
		}
		data.Set("client_id", strconv.Itoa(secretData.ClientId))
		data.Set("client_secret", secretData.ClientSecret)
		data.Set("grant_type", "authorization_code")
		data.Set("code", code)
		data.Set("redirect_uri", "http://localhost:8089/api/oauth/osu")

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
		req.Header.Add("Accept", "application/json")
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
		apiUrl = "https://osu.ppy.sh"
		resource = "api/v2/me/osu"

		u, _ = url2.ParseRequestURI(apiUrl)
		u.Path = resource
		urlStr = u.String()
		req, _ = http.NewRequest(http.MethodGet, urlStr, nil)
		req.Header.Add("Authorization", "Bearer"+" "+accessToken)
		req.Header.Add("Accept", "application/json")
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
		id := int(dataRead["id"].(float64))
		username := dataRead["username"].(string)

		render.JSON(w, r, OsuOAuthResponse{ // TODO: redirect here
			Response: resp.OK(),
			OsuId:    id,
			Username: username,
		})
		return
	}
}
