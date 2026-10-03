import re
from typing import List, Dict, Any

class StructureChunker:
    """
    Structure-aware / Recursive chunker.
    Splits along markdown structural boundaries (Headings -> Paragraphs -> Sentences).
    Keeps entire sections together when within max_words cap.
    """
    def __init__(self, max_words: int = 200, min_words: int = 25):
        self.max_words = max_words
        self.min_words = min_words
        self.strategy_name = f"structure_max{max_words}"

    def chunk_document(self, doc: Dict[str, Any]) -> List[Dict[str, Any]]:
        text = doc["text"]
        doc_id = doc["doc_id"]
        doc_title = doc.get("title", doc_id)
        
        # Split text into sections by Markdown headings (#, ##, ###, ====)
        heading_pattern = r'(?m)^(#{1,4}\s+.+|={3,}.+={3,})$'
        parts = re.split(heading_pattern, text)
        
        sections = []
        current_heading = doc_title
        
        i = 0
        while i < len(parts):
            part = parts[i].strip()
            if not part:
                i += 1
                continue
            
            # Check if this part is a heading
            if re.match(heading_pattern, part):
                current_heading = part.lstrip("#").strip("=").strip()
                i += 1
                content = parts[i].strip() if i < len(parts) else ""
                sections.append({"heading": current_heading, "content": content})
                i += 1
            else:
                sections.append({"heading": current_heading, "content": part})
                i += 1

        chunks = []
        chunk_idx = 0

        for sec in sections:
            heading = sec["heading"]
            content = sec["content"]
            if not content:
                continue

            sec_words = content.split()
            # If section fits comfortably under max_words, keep as a single semantic unit
            if len(sec_words) <= self.max_words:
                chunk_id = f"{doc_id}#struct_{self.max_words}w_c{chunk_idx:03d}"
                full_text = f"[{heading}]\n{content}"
                chunks.append({
                    "chunk_id": chunk_id,
                    "doc_id": doc_id,
                    "title": doc_title,
                    "heading": heading,
                    "strategy": f"Recursive Structure (Max={self.max_words}w)",
                    "word_count": len(full_text.split()),
                    "text": full_text
                })
                chunk_idx += 1
            else:
                # Break section into paragraphs
                paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
                buffer_paras = []
                buffer_words = 0

                for p in paragraphs:
                    p_word_count = len(p.split())
                    
                    # If paragraph itself is too huge, break by sentences
                    if p_word_count > self.max_words:
                        if buffer_paras:
                            # Flush current buffer
                            buf_text = "\n\n".join(buffer_paras)
                            chunk_id = f"{doc_id}#struct_{self.max_words}w_c{chunk_idx:03d}"
                            full_text = f"[{heading}]\n{buf_text}"
                            chunks.append({
                                "chunk_id": chunk_id,
                                "doc_id": doc_id,
                                "title": doc_title,
                                "heading": heading,
                                "strategy": f"Recursive Structure (Max={self.max_words}w)",
                                "word_count": len(full_text.split()),
                                "text": full_text
                            })
                            chunk_idx += 1
                            buffer_paras = []
                            buffer_words = 0

                        # Sentence-level splitting for large paragraphs
                        sentences = re.split(r'(?<=[.!?])\s+', p)
                        sent_buf = []
                        sent_words = 0
                        for s in sentences:
                            s_cnt = len(s.split())
                            if sent_words + s_cnt > self.max_words and sent_buf:
                                s_text = " ".join(sent_buf)
                                chunk_id = f"{doc_id}#struct_{self.max_words}w_c{chunk_idx:03d}"
                                full_text = f"[{heading}]\n{s_text}"
                                chunks.append({
                                    "chunk_id": chunk_id,
                                    "doc_id": doc_id,
                                    "title": doc_title,
                                    "heading": heading,
                                    "strategy": f"Recursive Structure (Max={self.max_words}w)",
                                    "word_count": len(full_text.split()),
                                    "text": full_text
                                })
                                chunk_idx += 1
                                sent_buf = [s]
                                sent_words = s_cnt
                            else:
                                sent_buf.append(s)
                                sent_words += s_cnt
                        
                        if sent_buf:
                            s_text = " ".join(sent_buf)
                            chunk_id = f"{doc_id}#struct_{self.max_words}w_c{chunk_idx:03d}"
                            full_text = f"[{heading}]\n{s_text}"
                            chunks.append({
                                "chunk_id": chunk_id,
                                "doc_id": doc_id,
                                "title": doc_title,
                                "heading": heading,
                                "strategy": f"Recursive Structure (Max={self.max_words}w)",
                                "word_count": len(full_text.split()),
                                "text": full_text
                            })
                            chunk_idx += 1
                    else:
                        if buffer_words + p_word_count > self.max_words and buffer_paras:
                            buf_text = "\n\n".join(buffer_paras)
                            chunk_id = f"{doc_id}#struct_{self.max_words}w_c{chunk_idx:03d}"
                            full_text = f"[{heading}]\n{buf_text}"
                            chunks.append({
                                "chunk_id": chunk_id,
                                "doc_id": doc_id,
                                "title": doc_title,
                                "heading": heading,
                                "strategy": f"Recursive Structure (Max={self.max_words}w)",
                                "word_count": len(full_text.split()),
                                "text": full_text
                            })
                            chunk_idx += 1
                            buffer_paras = [p]
                            buffer_words = p_word_count
                        else:
                            buffer_paras.append(p)
                            buffer_words += p_word_count

                # Flush leftover paragraph buffer
                if buffer_paras:
                    buf_text = "\n\n".join(buffer_paras)
                    chunk_id = f"{doc_id}#struct_{self.max_words}w_c{chunk_idx:03d}"
                    full_text = f"[{heading}]\n{buf_text}"
                    chunks.append({
                        "chunk_id": chunk_id,
                        "doc_id": doc_id,
                        "title": doc_title,
                        "heading": heading,
                        "strategy": f"Recursive Structure (Max={self.max_words}w)",
                        "word_count": len(full_text.split()),
                        "text": full_text
                    })
                    chunk_idx += 1

        return chunks
