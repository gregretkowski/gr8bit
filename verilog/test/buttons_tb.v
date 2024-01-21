module test();
    reg clk = 0;
    reg btn1 = 0;
    reg btn2 = 0;
    wire btn;
    wire reset;

    buttons #(2) uut(
        clk,
        btn1,
        btn2,
        btn,
        reset
    );

    always begin
        #1 clk = ~clk;
    end

    initial begin
        $display("Starting Test");
        $monitor("Reset Value %b", reset);
        $monitor("Button Value %b", btn);
        #1 btn2 = 1'b0;
        #5 btn1 = 1'b1;
        #5 btn1 = 1'b0;
        #5 btn1 = 1'b1;
        #5 btn1 = 1'b0;
        #1 btn1 = 1'b1;
        #1 btn1 = 1'b0;
        #1 btn1 = 1'b1;
        #1 btn1 = 1'b0;
        #1 btn1 = 1'b1;
        #1 btn1 = 1'b0;

        #1 btn2 = 1'b1;
        #800 btn2 = 1'b0;
        #100 ;
        $finish;
    end

    initial begin
        $dumpfile("buttons.vcd");
        $dumpvars(0,test);
    end
endmodule