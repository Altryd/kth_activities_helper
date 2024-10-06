package main

import (
	"fmt"
	"kth_activities_helper/internal/database"
	"net/http"
)

func helloHandler(w http.ResponseWriter, r *http.Request) {
	fmt.Fprint(w, "Здарова, заебал!")
}

func handleRequest() {
	http.HandleFunc("/", helloHandler)
	fmt.Println("Server is running on port 8080")
	err := http.ListenAndServe(":8080", nil)
	if err != nil {
		return
	}
}

func main() {
	database.Init()
	handleRequest()

}
