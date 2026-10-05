import re
import os

# ----------------- UI.R -----------------
with open('app/ui.R', 'r') as f:
    ui_code = f.read()

new_tab_ui = """
    # =============================================
    # TAB 3 — Gợi ý việc làm AI (Machine Learning)
    # =============================================
    , tabPanel(
      title = tagList(icon("brain"), "🎯 Gợi ý Việc Làm (AI)"),
      value = "recommendation_ai",
      
      tags$div(
        class = "reco-layout",
        style = "margin-top: 8px; padding: 20px;",
        
        tags$div(
          class = "glass-card",
          tags$h3("Tìm kiếm việc làm thông minh với AI"),
          tags$p("Hệ thống sử dụng AI (TF-IDF + Cosine Similarity) để tìm việc làm phù hợp nhất với mô tả của bạn."),
          
          fluidRow(
            column(12,
              textAreaInput("cv_input", "Paste CV hoặc Mô tả bản thân vào đây:", rows=6, 
                           placeholder="Ví dụ: Tôi là lập trình viên với 3 năm kinh nghiệm Python, Django, REST API...")
            )
          ),
          fluidRow(
            column(4, selectInput("filter_location", "Địa điểm:", c("Tất cả", "Hà Nội", "TP.HCM", "Đà Nẵng", "Remote", "Khác"))),
            column(4, selectInput("filter_level", "Cấp bậc:", c("Tất cả", "Fresher", "Junior", "Middle", "Senior", "Manager"))),
            column(4, sliderInput("filter_salary", "Lương tối thiểu (triệu VND):", 0, 100, 0, step=5))
          ),
          fluidRow(
            column(12,
              actionButton("btn_recommend", "🔍 Tìm việc phù hợp", class="btn-gradient", style="width: 200px;"),
              shinycssloaders::withSpinner(DT::dataTableOutput("recommend_table"), type=8, color="#667eea", size=0.5)
            )
          )
        )
      )
    ) # end tabPanel AI
"""

# Inject before the final `  ) # end tabsetPanel`
ui_code = ui_code.replace("    ) # end tabPanel Recommendation\n  ) # end tabsetPanel", "    ) # end tabPanel Recommendation\n" + new_tab_ui + "\n  ) # end tabsetPanel")

with open('app/ui.R', 'w') as f:
    f.write(ui_code)


# ----------------- SERVER.R -----------------
with open('app/server.R', 'r') as f:
    server_code = f.read()

new_server_code = """
  # ============================================================
  # ML RECOMMENDATION ENGINE (TAB 3)
  # ============================================================
  
  # Load Python module using reticulate
  ml_recommender <- reactiveVal(NULL)
  
  observe({
    tryCatch({
      # Load once
      if (is.null(ml_recommender())) {
        reticulate::use_condaenv("base", required = FALSE)
        sys <- reticulate::import("sys")
        if (!"recommendation" %in% sys$path) {
            sys$path <- c("recommendation", sys$path)
        }
        # Tạm chuyển working dir để model load đúng file
        old_wd <- getwd()
        # Set to project root to allow "database/..." paths
        model_mod <- reticulate::import("03_model")
        ml_recommender(model_mod$JobRecommender())
      }
    }, error = function(e) {
      message("Lỗi load Python: ", e$message)
    })
  })

  observeEvent(input$btn_recommend, {
    req(input$cv_input, ml_recommender())
    
    cv_text <- input$cv_input
    loc_filter <- if(input$filter_location == "Tất cả") NULL else input$filter_location
    lvl_filter <- if(input$filter_level == "Tất cả") NULL else input$filter_level
    sal_filter <- if(input$filter_salary == 0) NULL else input$filter_salary
    
    # Call python method
    rec <- ml_recommender()
    res_df <- rec$recommend_from_cv_text(
      cv_text = cv_text, 
      top_k = 20L,
      location_filter = loc_filter,
      level_filter = lvl_filter,
      salary_min_filter = sal_filter
    )
    
    output$recommend_table <- DT::renderDataTable({
      if (nrow(res_df) == 0) {
        return(DT::datatable(data.frame(Message = "Không có kết quả phù hợp.")))
      }
      
      display_df <- data.frame(
        Rank = res_df$rank,
        Score = paste0(round(res_df$score, 1), "%"),
        Job = res_df$title,
        Company = res_df$company_name,
        Location = res_df$location,
        Level = res_df$level,
        Salary = ifelse(!is.na(res_df$salary_min) & !is.na(res_df$salary_max),
                        paste0(res_df$salary_min, " - ", res_df$salary_max, " tr"), "Thương lượng"),
        Platform = sapply(res_df$platforms, function(x) paste(x, collapse=", ")),
        stringsAsFactors = FALSE
      )
      
      DT::datatable(display_df, 
        rownames = FALSE,
        options = list(pageLength = 10, scrollX = TRUE, dom = "lfrtip"),
        class = "display compact"
      )
    })
  })
"""

# Inject before the final Session cleanup
server_code = server_code.replace("  # ============================================================\n  # 5. SESSION CLEANUP", new_server_code + "\n  # ============================================================\n  # 5. SESSION CLEANUP")

with open('app/server.R', 'w') as f:
    f.write(server_code)

print("Patched UI.R and Server.R successfully.")
