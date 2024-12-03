package security

import (
	"net/http"
	"time"
)

func SetCookie(w http.ResponseWriter, name string, value string, expiration time.Time) {
	cookie := buildCookie(name, value, expiration.Second())
	// req.AddCookie(cookie)
	http.SetCookie(w, cookie)
	// http.SetCookie(c.Writer, cookie)
}

func ClearCookie(w http.ResponseWriter, name string) {
	cookie := buildCookie(name, "", -1)
	// req.AddCookie(cookie)
	http.SetCookie(w, cookie)
	// http.SetCookie(c.Writer, cookie)
}

func buildCookie(name string, value string, expires int) *http.Cookie {
	cookie := &http.Cookie{
		Name:     name,
		Value:    value,
		Path:     "/",
		HttpOnly: true,
		MaxAge:   expires,
		Secure:   true,
		SameSite: http.SameSiteLaxMode,
	}

	return cookie
}
